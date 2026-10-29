"""SIERRAH outfit recommendation engine.

Given the user's *actual* wardrobe and their preferences, the engine

1. scores every wardrobe piece against the occasion (tags, formality, suitable
   subcategories, fabric), the preferred style, comfort and colours;
2. builds candidate base outfits (separates, kurti sets, dresses, sarees...);
3. completes each one with footwear, a bag, jewellery and makeup, preferring the
   user's own pieces and falling back to demo-catalog suggestions that respect the
   budget; and
4. ranks the results, keeping the options distinct from each other.

Every number is explained in the response (``breakdown`` and ``whyItWorks``).
"""

from __future__ import annotations

import math
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field

from ...schemas import (
    LookPreferences,
    MissingItem,
    Outfit,
    OutfitItem,
    OutfitPiece,
    RecommendationRequest,
    RecommendationResponse,
    ScorePart,
    ShopProduct,
    WardrobeItem,
)
from ...utils import now_iso
from ..catalog import CatalogService, is_similar
from . import colors as clr
from .profiles import PROFILES, MakeupLook, HairLook, OccasionProfile, formality_of, keyword_in, resolve_occasion

ENGINE_VERSION = "2.0.0"

BUDGET_CAPS: dict[str, float] = {
    "under-500": 500.0,
    "500-1500": 1500.0,
    "1500-3000": 3000.0,
    "3000-plus": math.inf,
}

MIN_PIECE_FIT = 0.30  # below this a piece is not considered suitable for the occasion
MIN_CORE_FIT = 0.28

ETHNIC_WORDS = ("anarkali", "lehenga", "sharara", "kurta set", "kurti set", "suit", "saree", "sari", "gown")

# Points available for each part of the score (sums to 100).
MAX_POINTS = {"occasion": 35.0, "color": 17.0, "style": 13.0, "comfort": 10.0, "completeness": 15.0, "budget": 10.0}
OCCASION_GATE = 0.72  # occasion fit below this scales the whole score down
SLOT_WEIGHTS = {"outfit": 4.0, "footwear": 3.0, "bag": 2.5, "jewellery": 2.0, "makeup": 2.0, "hairstyle": 1.5}

GENERIC_SUGGESTIONS: dict[str, dict[str, str]] = {
    "footwear": {
        "college": "Comfortable sneakers or flats", "casual": "Easy sneakers or sandals",
        "office": "Block heels, loafers or flats", "wedding": "Embellished heels or juttis",
        "party": "Strappy or block heels", "travel": "Walking sneakers", "festival": "Juttis or ethnic sandals",
    },
    "bags": {
        "college": "A practical sling or tote bag", "casual": "A crossbody or sling bag",
        "office": "A structured tote or handbag", "wedding": "A clutch or potli",
        "party": "A mini clutch", "travel": "A zipped crossbody or backpack", "festival": "A potli bag",
    },
    "jewellery": {
        "college": "Small studs or a watch", "casual": "A watch or tiny studs",
        "office": "Minimal earrings and a watch", "wedding": "A coordinated necklace and jhumkas",
        "party": "Statement earrings", "travel": "Minimal studs", "festival": "Jhumkas or chandbalis",
    },
    "makeup": {k: "A simple makeup look" for k in PROFILES},
    "outfit": {
        "college": "A kurti or top with jeans or trousers", "casual": "A tee with jeans or an easy dress",
        "office": "A formal shirt or kurti with trousers", "wedding": "A saree, lehenga or festive ethnic set",
        "party": "A stylish dress or coordinated set", "travel": "Comfortable layers in breathable fabric",
        "festival": "A festive kurti set or saree",
    },
}

SLOT_FOR_CATEGORY = {"footwear": "footwear", "bags": "bag", "jewellery": "jewellery", "makeup": "makeup"}

STOPWORDS = {
    "the", "and", "for", "with", "any", "too", "much", "very", "please", "that", "this", "want",
    "wear", "outfit", "look", "something", "style", "some", "like", "more", "less", "also", "have",
    "need", "would", "should", "could", "just", "only", "from", "into", "than", "then", "them",
    "they", "what", "when", "will", "your", "mine", "make", "good", "nice", "feel", "feeling",
    "comfortable", "comfort", "comfy", "formal", "casual", "dressy",
}

NEGATION = re.compile(
    r"\b(?:no|avoid|without|skip|not|don'?t want|dont want|hate|never)\s+(?:any\s+|the\s+|my\s+|a\s+)?"
    r"([a-z][a-z\-]+)(?:\s+(?:or|and)\s+([a-z][a-z\-]+))?"
)


def _stem(word: str) -> str:
    word = word.lower()
    return word[:-1] if word.endswith("s") and len(word) > 3 else word


def _wordset(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z][a-z\-]+", text.lower())}


# =============================================================== data holders
@dataclass(frozen=True)
class Gear:
    """A wardrobe item or a catalog product, in one comparable shape."""

    uid: str
    source: str  # "wardrobe" | "shopping"
    name: str
    category: str
    subcategory: str
    colors: tuple[str, ...]
    styles: tuple[str, ...]
    occasions: tuple[str, ...]
    fabric: str
    comfort: int
    price: float | None
    image: str
    tags: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return f"{self.subcategory} {self.name}".lower()

    @property
    def main_color(self) -> str:
        return self.colors[0] if self.colors else ""

    @property
    def words(self) -> set[str]:
        return _wordset(" ".join([self.name, self.subcategory, self.fabric, *self.colors, *self.tags]))


def gear_from_item(item: WardrobeItem) -> Gear:
    return Gear(
        uid=item.id, source="wardrobe", name=item.name, category=item.category,
        subcategory=item.subcategory, colors=tuple(item.colors), styles=tuple(item.styles),
        occasions=tuple(item.occasions), fabric=item.fabric, comfort=item.comfort,
        price=item.price, image=item.image, tags=tuple(item.tags),
    )


def gear_from_product(product: ShopProduct) -> Gear:
    return Gear(
        uid=product.id, source="shopping", name=product.name, category=product.category,
        subcategory=product.subcategory, colors=tuple(product.colors), styles=tuple(product.styles),
        occasions=tuple(product.occasions), fabric=product.fabric, comfort=product.comfort,
        price=product.price, image=product.image,
    )


@dataclass
class Context:
    profile: OccasionProfile
    prefs: LookPreferences
    favourites: list[str]
    style: str | None
    traits: set[str]
    comfort_priority: float
    budget_cap: float
    wanted: set[str]
    wardrobe: list[Gear]
    catalog: CatalogService
    products: dict[str, ShopProduct] = field(default_factory=dict)
    fit_cache: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class Core:
    garments: list[Gear]
    missing_roles: list[str]
    mode: str
    score: float = 0.0

    @property
    def spend(self) -> float:
        return sum(g.price or 0 for g in self.garments if g.source == "shopping")


@dataclass
class Assembly:
    core: Core
    garments: list[Gear]
    footwear: Gear | None = None
    bag: Gear | None = None
    jewellery: list[Gear] = field(default_factory=list)
    makeup: list[Gear] = field(default_factory=list)
    makeup_look: MakeupLook | None = None
    hair_look: HairLook | None = None
    missing: list[MissingItem] = field(default_factory=list)
    unsuitable: dict[str, str] = field(default_factory=dict)
    spent: float = 0.0
    breakdown: list[ScorePart] = field(default_factory=list)
    score: float = 0.0
    harmony: float = 0.0
    favourites_found: list[str] = field(default_factory=list)


# ================================================================== scoring
def gear_formality(g: Gear) -> float:
    found = formality_of(g.subcategory) or formality_of(g.name)
    if found is not None:
        return found
    levels = [PROFILES[o].formality for o in g.occasions if o in PROFILES]
    return sum(levels) / len(levels) if levels else 3.0


def piece_fit(g: Gear, ctx: Context) -> float:
    """How suitable a single piece is for this occasion and these preferences (0..1)."""
    if g.uid in ctx.fit_cache:
        return ctx.fit_cache[g.uid]
    p = ctx.profile

    if ctx.profile.key in g.occasions:
        occasion = 1.0
    elif g.occasions:
        occasion = max(p.related.get(o, 0.0) for o in g.occasions)
    else:
        occasion = 0.4  # untagged: unknown, not a mismatch

    if ctx.style:
        style = 1.0 if ctx.style in g.styles else (0.35 if g.styles else 0.45)
    else:
        style = 0.6

    if g.category in ("makeup", "skincare"):
        fit = 0.65 * occasion + 0.2 * style + 0.15 * 0.6
    else:
        formality = max(0.0, 1.0 - abs(gear_formality(g) - p.formality) / 2.5)
        avoid_kw = p.avoid.get(g.category, ())
        prefer_kw = p.prefer.get(g.category, ())
        preference = 0.0 if keyword_in(g.text, avoid_kw) else (1.0 if keyword_in(g.text, prefer_kw) else 0.5)
        fabric_l = g.fabric.lower()
        if fabric_l and any(f in fabric_l for f in p.good_fabrics):
            fabric = 1.0
        elif fabric_l and any(f in fabric_l for f in p.avoid_fabrics):
            fabric = 0.1
        else:
            fabric = 0.6
        comfort = (g.comfort - 1) / 4
        w_comfort = 0.04 + 0.14 * ctx.comfort_priority
        weights = {"occ": 0.30, "form": 0.20, "pref": 0.20, "fab": 0.07, "style": 0.10, "comf": w_comfort}
        total = sum(weights.values())
        fit = (
            weights["occ"] * occasion + weights["form"] * formality + weights["pref"] * preference
            + weights["fab"] * fabric + weights["style"] * style + weights["comf"] * comfort
        ) / total
        if preference == 0.0:
            fit *= 0.45  # explicitly unsuitable for this occasion

    if ctx.wanted and g.words & ctx.wanted:
        fit = min(1.0, fit + 0.12)
    ctx.fit_cache[g.uid] = fit
    return fit


def _dominants(gears: list[Gear]) -> list[str]:
    return [g.main_color for g in gears if g.main_color]


def harmony_with(color: str, anchors: list[str]) -> float:
    if not color or not anchors:
        return 0.8
    return sum(clr.pair_harmony(color, a) for a in anchors) / len(anchors)


# ============================================================= notes parsing
def parse_notes(notes: str) -> tuple[set[str], set[str], bool]:
    """Return (excluded words, wanted words, wants_comfort) from free-text requirements."""
    text = (notes or "").lower()
    excluded: set[str] = set()
    for match in NEGATION.finditer(text):
        for group in match.groups():
            if group and group not in STOPWORDS:
                excluded.add(_stem(group))
    positive = NEGATION.sub(" ", text)
    wanted = {_stem(w) for w in re.findall(r"[a-z][a-z\-]{3,}", positive) if w not in STOPWORDS}
    wants_comfort = bool(re.search(r"comfort|comfy|relaxed|all.day|walk", text))
    return excluded, wanted, wants_comfort


# ================================================================== engine
class RecommendationEngine:
    def __init__(self, catalog: CatalogService) -> None:
        self.catalog = catalog

    # ---------------------------------------------------------- public API
    def recommend(
        self,
        request: RecommendationRequest,
        wardrobe: list[WardrobeItem],
        wardrobe_source: str,
    ) -> RecommendationResponse:
        request_id = f"req-{uuid.uuid4().hex[:12]}"
        occasion_key, matched_by_keyword = resolve_occasion(request.occasion, request.custom_occasion, request.notes)
        profile = PROFILES[occasion_key]
        label = (request.custom_occasion or "").strip() if request.occasion == "custom" else profile.label
        label = label or profile.label

        excluded, wanted, wants_comfort = parse_notes(request.notes)
        usable = [
            item for item in wardrobe
            if not (excluded and (gear_from_item(item).words & excluded))
        ]
        removed = len(wardrobe) - len(usable)

        pref_comfort = {"low": 0.15, "medium": 0.5, "high": 1.0}[request.comfort]
        if "comfortable" in request.traits or wants_comfort:
            pref_comfort = 1.0
        ctx = Context(
            profile=profile,
            prefs=self._preferences(request),
            favourites=list(request.colors),
            style=request.style,
            traits=set(request.traits),
            comfort_priority=min(1.0, 0.5 * profile.comfort_weight + 0.5 * pref_comfort),
            budget_cap=BUDGET_CAPS[request.budget],
            wanted=wanted,
            wardrobe=[gear_from_item(i) for i in usable],
            catalog=self.catalog,
            products={p.id: p for p in self.catalog.all()},
        )

        limitations: list[str] = []
        if request.occasion == "custom":
            if matched_by_keyword:
                limitations.append(
                    f"\"{label}\" is a custom occasion; it was styled like our {profile.label} occasion based on your wording."
                )
            else:
                limitations.append(
                    f"We did not recognise \"{label}\" as a known occasion, so it was styled with our Casual rules. "
                    "Add details in Special Requirements (for example \"formal\" or \"wedding\") to steer it."
                )
        if removed:
            limitations.append(f"Left out {removed} wardrobe item(s) that match what you asked to avoid.")
        if not ctx.wardrobe:
            limitations.append(
                "Your wardrobe has no usable items, so every piece below is a demo-catalog suggestion, not something you own."
            )

        cores = self._build_cores(ctx)
        chosen = sorted(self._select(cores, ctx, request.max_outfits), key=lambda a: -a.score)
        outfits = [self._to_outfit(a, i + 1, request_id, request, label, occasion_key, ctx) for i, a in enumerate(chosen)]

        limitations.extend(self._limitations(chosen, ctx, label))
        return RecommendationResponse(
            request_id=request_id,
            occasion=request.occasion,
            occasion_label=label,
            resolved_occasion=occasion_key,  # type: ignore[arg-type]
            wardrobe_source=wardrobe_source,  # type: ignore[arg-type]
            wardrobe_size=len(wardrobe),
            outfits=outfits,
            limitations=limitations,
            engine_version=ENGINE_VERSION,
            generated_at=now_iso(),
        )

    @staticmethod
    def _preferences(request: RecommendationRequest) -> LookPreferences:
        return LookPreferences(
            occasion=request.occasion, custom_occasion=request.custom_occasion, style=request.style,
            colors=request.colors, budget=request.budget, comfort=request.comfort,
            traits=request.traits, notes=request.notes,
        )

    # --------------------------------------------------------------- cores
    def _is_ethnic_set(self, g: Gear) -> bool:
        return g.category == "sarees" or (g.category in ("dresses", "kurtis") and keyword_in(g.text, ETHNIC_WORDS))

    def _mode(self, garments: list[Gear]) -> str:
        if len(garments) == 1:
            g = garments[0]
            if self._is_ethnic_set(g):
                return "ethnic"
            return "dress" if g.category == "dresses" else "separates"
        if any(g.category == "kurtis" for g in garments):
            return "kurti_set"
        return "separates"

    @staticmethod
    def _compat(garments: list[Gear]) -> tuple[float, float]:
        """(multiplier, deduction) for garments that do not belong together."""
        if len(garments) != 2:
            return 1.0, 0.0
        a, b = garments
        factor, deduction = 1.0, 0.0
        if (a.category == "kurtis" and "skirt" in b.text) or (b.category == "kurtis" and "skirt" in a.text):
            factor = 0.6  # a kurti is not styled with a skirt
        if abs(gear_formality(a) - gear_formality(b)) > 2.0:
            deduction = 0.1
        return factor, deduction

    def _core_score(self, core: Core, ctx: Context) -> float:
        if not core.garments:
            return 0.0
        fits = [piece_fit(g, ctx) for g in core.garments]
        base = sum(fits) / len(fits)
        base *= 1 - 0.15 * len(core.missing_roles)
        weight = ctx.profile.modes.get(core.mode, 0.3)
        score = base * (0.5 + 0.5 * weight)
        factor, deduction = self._compat(core.garments)
        return max(0.0, score * factor - deduction)

    def _candidates(self, ctx: Context, categories: tuple[str, ...], limit: int) -> list[Gear]:
        pool = [g for g in ctx.wardrobe if g.category in categories and piece_fit(g, ctx) >= MIN_CORE_FIT]
        pool.sort(key=lambda g: piece_fit(g, ctx), reverse=True)
        return pool[:limit]

    def _build_cores(self, ctx: Context) -> list[Core]:
        cores: list[Core] = []
        tops = self._candidates(ctx, ("tops",), 8)
        kurtis = self._candidates(ctx, ("kurtis",), 8)
        bottoms = self._candidates(ctx, ("bottoms",), 6)
        singles = self._candidates(ctx, ("dresses", "sarees"), 10)

        for g in singles:
            cores.append(Core([g], [], self._mode([g])))
        for g in kurtis:
            if self._is_ethnic_set(g):
                cores.append(Core([g], [], "ethnic"))
        for upper in [*tops, *kurtis]:
            if bottoms:
                for b in bottoms:
                    cores.append(Core([upper, b], [], self._mode([upper, b])))
            else:
                cores.append(Core([upper], ["bottom"], self._mode([upper, upper])))
        if not tops and not kurtis:
            for b in bottoms[:3]:
                cores.append(Core([b], ["top"], "separates"))

        for core in cores:
            core.score = self._core_score(core, ctx)
        cores.sort(key=lambda c: c.score, reverse=True)
        cores = cores[:40]

        # Offer catalog-based options when the wardrobe cannot dress this occasion well.
        best = cores[0].score if cores else 0.0
        tagged = any(ctx.profile.key in g.occasions for c in cores for g in c.garments)
        if best < 0.52 or (not tagged and ctx.profile.formality >= 3.9):
            cores.extend(self._shop_cores(ctx))
        if not cores:
            cores.append(Core([], ["outfit"], "separates"))
        return cores

    def _shop_cores(self, ctx: Context) -> list[Core]:
        """Base outfits built around a catalog piece (always affordable within the budget)."""
        results: list[Core] = []
        seen: set[str] = set()
        for keywords in ctx.profile.catalog_core:
            ranked = self._rank_products(ctx, tuple(c for c in ("tops", "kurtis", "bottoms", "dresses", "sarees")), keywords, [], limit=2)
            for g in ranked:
                if g.uid in seen:
                    continue
                seen.add(g.uid)
                if g.category in ("dresses", "sarees") or self._is_ethnic_set(g):
                    results.append(Core([g], [], self._mode([g])))
                elif g.category in ("tops", "kurtis"):
                    partners = self._candidates(ctx, ("bottoms",), 3)
                    if partners:
                        results.extend(Core([g, b], [], self._mode([g, b])) for b in partners)
                    else:
                        results.append(Core([g], ["bottom"], self._mode([g, g])))
                else:  # bottoms
                    partners = self._candidates(ctx, ("tops", "kurtis"), 3)
                    if partners:
                        results.extend(Core([t, g], [], self._mode([t, g])) for t in partners)
                    else:
                        results.append(Core([g], ["top"], "separates"))
        affordable = [c for c in results if c.spend <= ctx.budget_cap]
        if not affordable and results:
            cheapest = min(results, key=lambda c: c.spend)
            names = " + ".join(g.name for g in cheapest.garments if g.source == "shopping")
            ctx.notes.append(
                f"The closest suitable outfit to buy ({names}) costs about ₹{cheapest.spend:,.0f} in our demo catalog, "
                f"above your budget of {self._money(ctx.budget_cap)}. Raise the budget to see it, or borrow or rent one."
            )
        results = affordable
        for core in results:
            core.score = self._core_score(core, ctx) * 0.92  # owning beats buying, all else equal
        return results

    # ---------------------------------------------------------- catalog use
    @staticmethod
    def _occasion_relevance(g: Gear, ctx: Context) -> float:
        if ctx.profile.key in g.occasions:
            return 1.0
        return max((ctx.profile.related.get(o, 0.0) for o in g.occasions), default=0.0)

    def _rank_products(
        self,
        ctx: Context,
        categories: tuple[str, ...],
        keywords: tuple[str, ...],
        anchors: list[str],
        *,
        limit: int = 3,
        max_price: float | None = None,
        exclude: set[str] | None = None,
    ) -> list[Gear]:
        scored: list[tuple[float, Gear]] = []
        for product in ctx.catalog.all():
            if product.category not in categories or (exclude and product.id in exclude):
                continue
            if max_price is not None and product.price > max_price:
                continue
            gear = gear_from_product(product)
            if keywords and not keyword_in(gear.text, keywords):
                continue
            fit = piece_fit(gear, ctx)
            if fit < MIN_PIECE_FIT or self._occasion_relevance(gear, ctx) < 0.5:
                continue
            if any(
                owned.category == gear.category
                and is_similar(owned.subcategory, owned.name, gear.subcategory, gear.name)
                and piece_fit(owned, ctx) >= MIN_PIECE_FIT
                for owned in ctx.wardrobe
            ):
                continue  # the user already owns a suitable one
            score = fit + 0.3 * harmony_with(gear.main_color, anchors)
            if ctx.favourites and clr.matches_any(list(gear.colors), ctx.favourites):
                score += 0.15
            score -= 0.05 * min(1.0, (gear.price or 0) / 3000)
            scored.append((score, gear))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [g for _, g in scored[:limit]]

    def _suggest(
        self,
        ctx: Context,
        categories: tuple[str, ...],
        anchors: list[str],
        remaining: float,
        used: set[str],
        keywords: tuple[str, ...] = (),
    ) -> tuple[Gear | None, list[Gear], Gear | None]:
        """Return (affordable suggestion, cheaper alternatives, cheapest option if none fits)."""
        ranked = self._rank_products(ctx, categories, keywords, anchors, limit=8, exclude=used)
        affordable = [g for g in ranked if (g.price or 0) <= remaining]
        if not affordable:
            cheapest = min(ranked, key=lambda g: g.price or 0, default=None)
            return None, [], cheapest
        pick = affordable[0]
        alternatives = [
            g for g in ranked
            if g.uid != pick.uid and (g.price or 0) < (pick.price or 0) and (g.price or 0) <= remaining
        ][:2]
        if not alternatives:
            pool = self._rank_products(ctx, categories, (), anchors, limit=8, exclude=used | {pick.uid}, max_price=remaining)
            alternatives = [g for g in pool if (g.price or 0) <= (pick.price or 0)][:2]
        return pick, alternatives, None

    # --------------------------------------------------------- assembling
    def _best_wardrobe(
        self, ctx: Context, category: str, anchors: list[str], used: Counter, *, count: int = 1
    ) -> tuple[list[Gear], str | None]:
        """Pick the best owned pieces of a category. Returns (chosen, best unsuitable name)."""
        pool = [g for g in ctx.wardrobe if g.category == category]
        scored: list[tuple[float, Gear]] = []
        for g in pool:
            fit = piece_fit(g, ctx)
            score = fit + 0.28 * harmony_with(g.main_color, anchors) - 0.12 * used[g.uid]
            if ctx.favourites and clr.matches_any(list(g.colors), ctx.favourites):
                score += 0.08
            scored.append((score, g))
        scored.sort(key=lambda s: s[0], reverse=True)
        suitable = [g for _, g in scored if piece_fit(g, ctx) >= MIN_PIECE_FIT]
        chosen: list[Gear] = []
        seen_kinds: set[str] = set()
        for g in suitable:
            kind = (g.subcategory or g.name).lower()
            if kind in seen_kinds:
                continue
            seen_kinds.add(kind)
            chosen.append(g)
            if len(chosen) == count:
                break
        unsuitable = scored[0][1].name if (pool and not chosen) else None
        return chosen, unsuitable

    def _assemble(self, core: Core, ctx: Context, used: Counter, rank_hint: int) -> Assembly | None:
        remaining = ctx.budget_cap - core.spend
        if remaining < 0:
            return None
        asm = Assembly(core=core, garments=list(core.garments), spent=core.spend)
        shop_used: set[str] = {g.uid for g in core.garments if g.source == "shopping"}
        anchors = _dominants(asm.garments)

        # ---- fill missing base-outfit roles from the catalog ----
        for role in core.missing_roles:
            categories: tuple[str, ...] = {
                "bottom": ("bottoms",), "top": ("tops", "kurtis"), "outfit": ("dresses", "sarees", "kurtis", "tops"),
            }[role]
            pick, alternatives, cheapest = self._suggest(ctx, categories, anchors, remaining, shop_used)
            if pick:
                asm.garments.append(pick)
                asm.spent += pick.price or 0
                remaining -= pick.price or 0
                shop_used.add(pick.uid)
                anchors = _dominants(asm.garments)
                asm.missing.append(self._missing("outfit", pick.category, f"A {role} to complete this outfit", pick, alternatives, True, ctx))
            else:
                asm.missing.append(self._unaffordable("outfit", categories[0], f"A {role} to complete this outfit", cheapest, remaining, ctx))
        if not asm.garments:
            asm.unsuitable["outfit"] = ""

        # ---- footwear / bag ----
        for category, slot, attr in (("footwear", "footwear", "footwear"), ("bags", "bag", "bag")):
            chosen, unsuitable = self._best_wardrobe(ctx, category, anchors, used)
            if chosen:
                setattr(asm, attr, chosen[0])
                continue
            if unsuitable:
                asm.unsuitable[slot] = unsuitable
            pick, alternatives, cheapest = self._suggest(ctx, (category,), anchors, remaining, shop_used)
            reason = self._missing_reason(slot, unsuitable, ctx)
            if pick:
                setattr(asm, attr, pick)
                asm.spent += pick.price or 0
                remaining -= pick.price or 0
                shop_used.add(pick.uid)
                asm.missing.append(self._missing(slot, category, reason, pick, alternatives, True, ctx))
            else:
                asm.missing.append(self._unaffordable(slot, category, reason, cheapest, remaining, ctx))

        # ---- jewellery ----
        if ctx.profile.wants_jewellery:
            chosen, unsuitable = self._best_wardrobe(ctx, "jewellery", anchors, used, count=2)
            if chosen:
                asm.jewellery = chosen
            else:
                if unsuitable:
                    asm.unsuitable["jewellery"] = unsuitable
                pick, alternatives, cheapest = self._suggest(ctx, ("jewellery",), anchors, remaining, shop_used)
                reason = self._missing_reason("jewellery", unsuitable, ctx)
                if pick:
                    asm.jewellery = [pick]
                    asm.spent += pick.price or 0
                    remaining -= pick.price or 0
                    shop_used.add(pick.uid)
                    asm.missing.append(self._missing("jewellery", "jewellery", reason, pick, alternatives, True, ctx))
                else:
                    asm.missing.append(self._unaffordable("jewellery", "jewellery", reason, cheapest, remaining, ctx))

        # ---- makeup ----
        lip_anchor = anchors[:1]
        pool = [g for g in ctx.wardrobe if g.category == "makeup" and piece_fit(g, ctx) >= MIN_PIECE_FIT]
        pool.sort(key=lambda g: piece_fit(g, ctx) - 0.1 * used[g.uid], reverse=True)
        picked_kinds: set[str] = set()
        for g in pool:
            kind = (g.subcategory or g.name).lower()
            if kind in picked_kinds:
                continue
            if "lip" in kind and lip_anchor and harmony_with(g.main_color, lip_anchor) < 0.6:
                continue  # skip a lip colour that clashes with the outfit
            picked_kinds.add(kind)
            asm.makeup.append(g)
            if len(asm.makeup) == 3:
                break
        if not asm.makeup:
            pick, alternatives, cheapest = self._suggest(ctx, ("makeup",), anchors, remaining, shop_used)
            reason = "Makeup to finish the look"
            if pick:
                asm.makeup = [pick]
                asm.spent += pick.price or 0
                remaining -= pick.price or 0
                shop_used.add(pick.uid)
                asm.missing.append(self._missing("makeup", "makeup", reason, pick, alternatives, True, ctx))
            else:
                asm.missing.append(self._unaffordable("makeup", "makeup", reason, cheapest, remaining, ctx))

        asm.makeup_look = self._pick_look(ctx.profile.makeup, ctx, rank_hint)
        asm.hair_look = self._pick_look(ctx.profile.hair, ctx, rank_hint)
        self._score(asm, ctx)
        return asm

    def _pick_look(self, options, ctx: Context, rank_hint: int):
        """Choose a makeup/hair option that fits the user's vibe, rotating for variety."""
        if not options:
            return None
        vibe = set(ctx.traits) | ({ctx.style} if ctx.style else set())
        scored = [(len(set(o.vibe) & vibe), i, o) for i, o in enumerate(options)]
        scored.sort(key=lambda s: (-s[0], s[1]))
        top_score = scored[0][0]
        tied = [s for s in scored if s[0] == top_score]
        pool = tied if len(tied) > 1 else scored
        return pool[rank_hint % len(pool)][2]

    # ------------------------------------------------- missing-item objects
    def _product(self, gear: Gear, ctx: Context) -> ShopProduct:
        return ctx.products[gear.uid]

    def _missing(
        self, slot: str, category: str, reason: str, pick: Gear, alternatives: list[Gear],
        within_budget: bool, ctx: Context,
    ) -> MissingItem:
        return MissingItem(
            slot=slot,  # type: ignore[arg-type]
            category=category,
            label=pick.name,
            reason=reason,
            suggestion=self._product(pick, ctx),
            alternatives=[self._product(a, ctx) for a in alternatives],
            within_budget=within_budget,
        )

    def _unaffordable(
        self, slot: str, category: str, reason: str, cheapest: Gear | None, remaining: float, ctx: Context
    ) -> MissingItem:
        generic = GENERIC_SUGGESTIONS.get(category if category != "bags" else "bags", {}).get(
            ctx.profile.key, "A suitable piece"
        )
        if cheapest is not None:
            note = (
                f"{reason}. The closest demo-catalog option is {cheapest.name} (₹{cheapest.price:,.0f}), "
                f"which is above the remaining budget of {self._money(remaining)}."
            )
        else:
            note = f"{reason}. Nothing in the demo catalog suits this occasion yet; look for {generic.lower()}."
        return MissingItem(slot=slot, category=category, label=generic, reason=note, suggestion=None, within_budget=False)  # type: ignore[arg-type]

    @staticmethod
    def _money(value: float) -> str:
        return "unlimited" if math.isinf(value) else f"₹{max(value, 0):,.0f}"

    @staticmethod
    def _missing_reason(slot: str, unsuitable: str | None, ctx: Context) -> str:
        if unsuitable:
            return f"Your {unsuitable} is not a good match for {ctx.profile.label.lower()}"
        return f"You have no {slot} in your wardrobe yet"

    # ------------------------------------------------------------- scoring
    def _score(self, asm: Assembly, ctx: Context) -> None:
        garments = asm.garments
        accessories = [g for g in [asm.footwear, asm.bag, *asm.jewellery] if g]
        everything = garments + accessories

        # Occasion fit
        core_fit = (sum(piece_fit(g, ctx) for g in garments) / len(garments)) if garments else 0.0
        weight = ctx.profile.modes.get(asm.core.mode, 0.3)
        core_fit *= 0.5 + 0.5 * weight
        core_fit *= 1 - 0.1 * len(asm.core.missing_roles)
        factor, deduction = self._compat(garments)
        core_fit = max(0.0, core_fit * factor - deduction)
        acc_fit = (sum(piece_fit(g, ctx) for g in accessories) / len(accessories)) if accessories else 0.3
        occasion = 0.7 * core_fit + 0.3 * acc_fit

        # Colour
        groups = [list(g.colors) for g in garments + [x for x in (asm.footwear, asm.bag) if x] if g.colors]
        asm.harmony = clr.outfit_harmony(groups)
        all_colors = [c for g in everything for c in g.colors]
        asm.favourites_found = clr.matches_any(all_colors, ctx.favourites)
        if ctx.favourites:
            fav_part = len(asm.favourites_found) / min(len(ctx.favourites), 2)
            color = 0.65 * asm.harmony + 0.35 * min(1.0, fav_part)
        else:
            color = asm.harmony

        # Style
        wanted_style = ctx.style
        vibe = ctx.traits & {"minimal", "trendy", "simple"}
        if wanted_style or vibe:
            hits = 0.0
            for g in everything:
                if wanted_style and wanted_style in g.styles:
                    hits += 1.0
                elif vibe and (set(g.tags) & vibe):
                    hits += 0.6
                else:
                    hits += 0.25 if not g.styles else 0.0
            style = hits / len(everything) if everything else 0.4
        else:
            style = 0.75

        # Comfort
        comfort_pieces = [g.comfort for g in garments + [x for x in (asm.footwear,) if x]] or [3]
        c = (sum(comfort_pieces) / len(comfort_pieces) - 1) / 4
        comfort = 1 - ctx.comfort_priority * (1 - c)

        # Completeness
        slot_credit = {
            "outfit": 1.0 if garments and not asm.core.missing_roles else (0.7 if garments else 0.0),
            "footwear": self._credit(asm.footwear),
            "bag": self._credit(asm.bag),
            "jewellery": min(1.0, max((self._credit(j) for j in asm.jewellery), default=0.0)) if ctx.profile.wants_jewellery else 1.0,
            "makeup": max((self._credit(m) for m in asm.makeup), default=0.35),
            "hairstyle": 1.0,
        }
        # A shop-bought base outfit counts as bought, not owned.
        if garments and all(g.source == "shopping" for g in garments):
            slot_credit["outfit"] = 0.7
        elif garments and any(g.source == "shopping" for g in garments):
            slot_credit["outfit"] = 0.85
        completeness = sum(SLOT_WEIGHTS[s] * v for s, v in slot_credit.items()) / sum(SLOT_WEIGHTS.values())

        # Budget
        if asm.spent <= 0:
            budget = 1.0
        elif math.isinf(ctx.budget_cap):
            budget = 1.0 - 0.4 * min(1.0, asm.spent / 5000)
        else:
            budget = 1.0 - 0.6 * min(1.0, asm.spent / ctx.budget_cap)

        parts = [
            ("occasion", "Occasion fit", occasion),
            ("color", "Colour harmony", color),
            ("style", "Style match", style),
            ("comfort", "Comfort", comfort),
            ("completeness", "Complete look", completeness),
            ("budget", "Budget friendliness", budget),
        ]
        asm.breakdown = [
            ScorePart(key=k, label=lbl, points=round(MAX_POINTS[k] * max(0.0, min(1.0, v)), 1), max_points=MAX_POINTS[k])
            for k, lbl, v in parts
        ]
        raw = sum(p.points for p in asm.breakdown)
        # Looking good is not enough: a look that does not suit the occasion is scaled down.
        gate = min(1.0, occasion / OCCASION_GATE) if OCCASION_GATE else 1.0
        if gate < 1.0:
            asm.breakdown.append(
                ScorePart(key="gate", label="Occasion suitability adjustment", points=round(-(raw * (1 - gate)), 1), max_points=0)
            )
        asm.score = round(max(0.0, sum(p.points for p in asm.breakdown)), 1)

    @staticmethod
    def _credit(gear: Gear | None) -> float:
        if gear is None:
            return 0.0
        return 1.0 if gear.source == "wardrobe" else 0.7

    # ------------------------------------------------------------ selection
    def _select(self, cores: list[Core], ctx: Context, count: int) -> list[Assembly]:
        chosen: list[Assembly] = []
        used: Counter = Counter()
        remaining = list(cores)
        while remaining and len(chosen) < count:
            best: tuple[float, Assembly, Core] | None = None
            for core in remaining:
                asm = self._assemble(core, ctx, used, rank_hint=len(chosen))
                if asm is None:
                    continue
                overlap = sum(1 for g in core.garments if used[g.uid] > 0)
                adjusted = asm.score - 7.0 * overlap
                if best is None or adjusted > best[0]:
                    best = (adjusted, asm, core)
            if best is None:
                break
            _, asm, core = best
            if chosen and (asm.score < 0.72 * chosen[0].score or asm.score < 35):
                break
            chosen.append(asm)
            remaining.remove(core)
            for g in asm.garments:
                used[g.uid] += 2
            for g in [asm.footwear, asm.bag, *asm.jewellery, *asm.makeup]:
                if g:
                    used[g.uid] += 1
        if not chosen:  # nothing could be built within budget: return an honest, tip-only outfit
            empty = Core([], ["outfit"], "separates")
            empty_asm = Assembly(core=empty, garments=[])
            empty_asm.makeup_look = self._pick_look(ctx.profile.makeup, ctx, 0)
            empty_asm.hair_look = self._pick_look(ctx.profile.hair, ctx, 0)
            empty_asm.missing.append(
                self._unaffordable("outfit", "outfit", "An outfit for this occasion", None, ctx.budget_cap, ctx)
            )
            self._score(empty_asm, ctx)
            chosen.append(empty_asm)
        return chosen

    # ----------------------------------------------------- response objects
    @staticmethod
    def _piece(g: Gear) -> OutfitPiece:
        image = "" if g.image.startswith("data:") else g.image
        return OutfitPiece(
            category=g.category,  # type: ignore[arg-type]
            name=g.name,
            subcategory=g.subcategory,
            colors=list(g.colors),
            fabric=g.fabric,
            image=image,
            source=g.source,  # type: ignore[arg-type]
            wardrobe_item_id=g.uid if g.source == "wardrobe" else None,
            shop_item_id=g.uid if g.source == "shopping" else None,
            price=g.price if g.source == "shopping" else None,
        )

    @staticmethod
    def _describe(g: Gear) -> str:
        return " ".join(filter(None, [", ".join(g.colors), g.fabric.lower()])).strip()

    def _slot_item(self, slot: str, gears: list[Gear], fallback: str, category: str, detail_extra: str = "") -> OutfitItem:
        if not gears:
            return OutfitItem(slot=slot, title=fallback, category=category, detail=detail_extra, source="tip")  # type: ignore[arg-type]
        pieces = [self._piece(g) for g in gears]
        bought = [g for g in gears if g.source == "shopping"]
        owned = [g for g in gears if g.source == "wardrobe"]
        # Any suggested piece makes the whole slot "shopping", so a purchase is never shown as owned.
        source = "shopping" if bought else "wardrobe"
        detail_parts = []
        if bought:
            total = sum(g.price or 0 for g in bought)
            if owned:
                detail_parts.append(f"You own: {', '.join(g.name for g in owned)}")
            detail_parts.append(
                f"Suggested purchase: {', '.join(g.name for g in bought)} · demo price ₹{total:,.0f}"
            )
        else:
            desc = " + ".join(self._describe(g) for g in gears if self._describe(g))
            if desc:
                detail_parts.append(desc)
        if detail_extra:
            detail_parts.append(detail_extra)
        first_image = next((p.image for p in pieces if p.image), "")
        return OutfitItem(
            slot=slot,  # type: ignore[arg-type]
            title=" + ".join(g.name for g in gears),
            category=category,
            detail=" · ".join(detail_parts),
            image=first_image,
            source=source,  # type: ignore[arg-type]
            pieces=pieces,
            wardrobe_item_ids=[g.uid for g in owned],
            shop_item_id=bought[0].uid if bought else None,
        )

    def _to_outfit(
        self, asm: Assembly, rank: int, request_id: str, request: RecommendationRequest,
        label: str, occasion_key: str, ctx: Context,
    ) -> Outfit:
        generic = GENERIC_SUGGESTIONS
        items: list[OutfitItem] = []
        outfit_fallback = generic["outfit"].get(occasion_key, "An outfit for this occasion")
        items.append(self._slot_item("outfit", asm.garments, outfit_fallback, "outfit",
                                     detail_extra="" if asm.garments else "Nothing suitable is in your wardrobe"))
        items.append(self._slot_item("footwear", [asm.footwear] if asm.footwear else [],
                                     generic["footwear"].get(occasion_key, "Suitable footwear"), "footwear",
                                     "" if asm.footwear else self._tip_detail("footwear", asm, ctx)))
        items.append(self._slot_item("bag", [asm.bag] if asm.bag else [],
                                     generic["bags"].get(occasion_key, "A suitable bag"), "bags",
                                     "" if asm.bag else self._tip_detail("bag", asm, ctx)))
        items.append(self._slot_item("jewellery", asm.jewellery,
                                     generic["jewellery"].get(occasion_key, "Simple jewellery"), "jewellery",
                                     "" if asm.jewellery else self._tip_detail("jewellery", asm, ctx)))
        items.append(self._makeup_item(asm, ctx))
        items.append(self._hair_item(asm, ctx))

        total = round(asm.spent, 2)
        outfit_title = f"{label} {self._style_word(request.style)}Look".replace("  ", " ").strip()
        if asm.garments:
            outfit_title = f"{outfit_title} · {' + '.join(g.name for g in asm.garments)}"[:120]
        return Outfit(
            id=f"out-{uuid.uuid4().hex[:12]}",
            request_id=request_id,
            rank=rank,
            title=outfit_title,
            score=asm.score,
            score_label=self._score_label(asm.score),
            breakdown=asm.breakdown,
            why_it_works=self._explain(asm, ctx, label),
            occasion=request.occasion,
            occasion_label=label,
            resolved_occasion=occasion_key,  # type: ignore[arg-type]
            preferences=ctx.prefs,
            appearance=request.appearance,
            items=items,
            accessories=[self._piece(g) for g in [asm.bag, *asm.jewellery] if g],
            styling_tips=self._tips(asm, ctx, label),
            missing_items=asm.missing,
            suggested_total=total,
            budget_max=None if math.isinf(ctx.budget_cap) else ctx.budget_cap,
            image=None,
            generated_at=now_iso(),
        )

    @staticmethod
    def _style_word(style: str | None) -> str:
        return f"{style.capitalize()} " if style else ""

    @staticmethod
    def _score_label(score: float) -> str:
        if score >= 85:
            return "Excellent match"
        if score >= 72:
            return "Great match"
        if score >= 58:
            return "Good match"
        if score >= 45:
            return "Workable match"
        return "Limited match"

    def _tip_detail(self, slot: str, asm: Assembly, ctx: Context) -> str:
        miss = next((m for m in asm.missing if m.slot == slot), None)
        return miss.reason if miss else ""

    def _makeup_item(self, asm: Assembly, ctx: Context) -> OutfitItem:
        look = asm.makeup_look
        title = look.name if look else "Makeup"
        description = look.description if look else ""
        owned = [g for g in asm.makeup if g.source == "wardrobe"]
        bought = [g for g in asm.makeup if g.source == "shopping"]
        pieces = [self._piece(g) for g in asm.makeup]
        detail = description
        if owned:
            detail += f" · Uses your {', '.join(g.name for g in owned)}"
        if bought:
            detail += f" · Suggested purchase: {', '.join(g.name for g in bought)} (demo ₹{sum(g.price or 0 for g in bought):,.0f})"
        image = next((p.image for p in pieces if p.image), "/images/look/makeup.jpg")
        return OutfitItem(
            slot="makeup", title=title, category="makeup", detail=detail.strip(" ·"),
            image=image, source="wardrobe" if owned else ("shopping" if bought else "tip"),
            pieces=pieces, wardrobe_item_ids=[g.uid for g in owned],
            shop_item_id=bought[0].uid if bought else None,
        )

    def _hair_item(self, asm: Assembly, ctx: Context) -> OutfitItem:
        look = asm.hair_look
        serum = next(
            (g for g in ctx.wardrobe if g.category == "skincare" and keyword_in(g.text, ("hair", "serum"))), None
        )
        detail = look.description if look else ""
        if serum:
            detail += f" · Finish with your {serum.name}"
        return OutfitItem(
            slot="hairstyle", title=look.name if look else "Hairstyle", category="hairstyle",
            detail=detail.strip(" ·"), image="/images/look/hairstyle.jpg", source="tip",
        )

    # --------------------------------------------------------- explanations
    def _explain(self, asm: Assembly, ctx: Context, label: str) -> list[str]:
        p = ctx.profile
        reasons: list[str] = []
        core_names = " + ".join(g.name for g in asm.garments) or "an outfit"
        tagged = [g.name for g in asm.garments if p.key in g.occasions]
        if tagged:
            reasons.append(f"{core_names}: you tagged {', '.join(tagged)} for {p.label.lower()}, and it fits the {p.label.lower()} dress level.")
        elif asm.garments:
            reasons.append(
                f"{core_names} is the closest match in your wardrobe for {label.lower()} based on formality, fabric and cut."
            )
        else:
            reasons.append(f"Nothing in your wardrobe suits {label.lower()} yet, so this look is built from suggestions.")

        if asm.garments:
            if asm.harmony >= 0.8:
                reasons.append("The colours sit well together: neutrals and tonal shades keep it cohesive.")
            elif asm.harmony >= 0.6:
                reasons.append("The colours work together with a little contrast; keep accessories simple.")
            else:
                reasons.append("The colours are on the bold side together, so keep accessories neutral.")
        if asm.favourites_found:
            reasons.append(f"Includes your favourite colour{'s' if len(asm.favourites_found) > 1 else ''}: {', '.join(asm.favourites_found)}.")
        elif ctx.favourites:
            reasons.append(f"None of your wardrobe pieces for this look are {' or '.join(ctx.favourites)}, so colour was matched on harmony instead.")

        if ctx.style:
            hits = [g.name for g in asm.garments if ctx.style in g.styles]
            if hits:
                reasons.append(f"Matches your {ctx.style} style preference ({', '.join(hits)}).")
            elif asm.garments:
                reasons.append(f"None of the main pieces are tagged {ctx.style}, so this is the best fit on other factors.")

        if ctx.comfort_priority >= 0.7 and asm.garments:
            avg = sum(g.comfort for g in asm.garments) / len(asm.garments)
            if avg >= 3.5:
                reasons.append(f"Comfort matters here, and the main pieces average {avg:.1f}/5 for comfort.")
            else:
                reasons.append(
                    f"Comfort matters here, but the best-fitting main pieces average {avg:.1f}/5 for comfort; "
                    "rate your items' comfort in My Wardrobe to improve this."
                )

        for slot, name in asm.unsuitable.items():
            if name:
                reasons.append(f"Your {name} was left out because it is not a good match for {label.lower()}.")

        if asm.spent <= 0:
            reasons.append("Built entirely from pieces you already own. Nothing to buy.")
        else:
            reasons.append(
                f"Optional purchases total ₹{asm.spent:,.0f} (demo prices), within your budget of {self._money(ctx.budget_cap)}."
            )
        if ctx.profile.accessory_note:
            reasons.append(ctx.profile.accessory_note)
        return reasons

    def _tips(self, asm: Assembly, ctx: Context, label: str) -> list[str]:
        tips = list(ctx.profile.tips)
        if asm.favourites_found:
            tips.append(
                f"You picked {', '.join(asm.favourites_found)}. Repeat it in a small accessory such as a lip colour or bag for a cohesive finish."
            )
        elif ctx.favourites:
            tips.append(f"You like {', '.join(ctx.favourites)}. Try adding it through a scarf, dupatta or nail colour.")
        if ctx.prefs.notes.strip():
            tips.append(f"Noted: \"{ctx.prefs.notes.strip()}\". We used this to rank and filter pieces.")
        if asm.footwear and asm.footwear.comfort <= 2 and ctx.comfort_priority >= 0.5:
            tips.append(f"Your {asm.footwear.name} are dressy but less comfortable; carry flats for later if you will be on your feet.")
        return tips

    def _limitations(self, chosen: list[Assembly], ctx: Context, label: str) -> list[str]:
        notes: list[str] = []
        if not chosen:
            return notes
        top = chosen[0]
        notes.extend(ctx.notes)
        wardrobe_cores = [a for a in chosen if a.garments and all(g.source == "wardrobe" for g in a.garments)]
        untagged = [a for a in wardrobe_cores if not any(ctx.profile.key in g.occasions for g in a.garments)]
        if wardrobe_cores and len(untagged) == len(wardrobe_cores) and ctx.profile.formality >= 3.9:
            notes.append(
                f"None of your garments are tagged for {label.lower()}, so the wardrobe options below are the closest "
                "matches by dress level, fabric and cut. A saree, lehenga or festive ethnic set would suit it best; "
                "add one to My Wardrobe and tag it for this occasion."
            )
        if not wardrobe_cores and ctx.wardrobe:
            notes.append(
                f"Your wardrobe has no strong {label.lower()} outfit, so the base outfit is a suggested purchase. "
                "Add suitable pieces in My Wardrobe to get looks built entirely from what you own."
            )
        elif wardrobe_cores and top.score < 58:
            notes.append(
                f"Your wardrobe is only a partial match for {label.lower()}. These are the best options you own; "
                "tag your pieces with the right occasion or add more to improve the result."
            )
        if any(not m.within_budget for a in chosen for m in a.missing):
            notes.append("Some missing items could not be suggested within your budget. Raise the budget or borrow or rent them.")
        if len(chosen) < 2 and len(ctx.wardrobe) > 3:
            notes.append("Only one distinct outfit could be built with your current wardrobe for this occasion.")
        return notes
