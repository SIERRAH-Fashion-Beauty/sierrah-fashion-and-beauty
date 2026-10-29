# SIERRAH – Fashion & Beauty

> **Your Style. Your Beauty. Your Way.**

SIERRAH is an AI-powered fashion and beauty styling platform that helps users create personalized outfits using their existing wardrobe. Choose an occasion, get outfit and accessory recommendations, preview complete looks with AI-generated models, and discover budget-friendly shopping options, all in one place.

People often feel they have nothing to wear even with a full wardrobe. SIERRAH styles what you already own for college, office, weddings, parties, travel and festivals, and only suggests a purchase when a look genuinely needs something.

## Screens

| # | Screen | Route | What it does |
|---|--------|-------|--------------|
| 1 | Home | `/` | Editorial hero, **Start Styling**, circular quick links |
| 2 | My Wardrobe | `/wardrobe` | Category filters, search, upload photo, add / edit / remove items, **Save Wardrobe** |
| 3 | Choose Your Occasion | `/style` | College, Casual, Office, Wedding, Party, Travel, Festival, Custom |
| 4 | Personalize Your Look | `/personalize` | Style, colours, budget, preferences, special requirements |
| 5 | Your Personalized Look | `/look` | Model image plus Outfit / Footwear / Bag / Jewellery / Makeup / Hairstyle, with a "from your wardrobe" or "suggested" label on each |
| 6 | Complete Look Preview | `/preview` | Centered model, item cards, styling tips, Save and favorite |
| 7 | Smart Shopping Suggestions | `/shopping` | Missing items, category and budget filters, **demo** prices |
| 8 | My Saved Looks | `/saved` | Occasion and favorite filters, reopen, delete |
| – | Profile | `/profile` | Stats, backend connection status, reset demo data |

## Tech stack

- **Frontend:** React 19 + Vite + TypeScript, Tailwind CSS 3, Lucide React, React Router
- **Backend:** Python FastAPI, Pydantic v2, SQLite (standard-library `sqlite3`)
- **State:** one shared `AppContext` (reducer) persisted to `localStorage`, synced to the API when it is reachable

## Project structure

```
sierrah-fashion-and-beauty/
├── frontend/
│   ├── public/images/        # Editorial model photos, wardrobe + shop product images, logo
│   ├── src/
│   │   ├── components/       # layout/, ui/, wardrobe/, look/
│   │   ├── context/          # AppContext (shared state, persistence, sync)
│   │   ├── data/             # demo wardrobe, occasions, options, shop catalog
│   │   ├── lib/              # stylist engine, storage, image helpers
│   │   ├── pages/            # the 8 screens + profile
│   │   ├── services/         # api.ts (VITE_API_BASE_URL), lookImage.ts
│   │   └── types/
│   ├── .env.example
│   └── package.json, vite.config.ts, tailwind.config.js, tsconfig.json
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app, CORS, routers
│   │   ├── database.py       # SQLite schema + one-time demo seed
│   │   ├── schemas.py        # Pydantic models (camelCase JSON)
│   │   ├── routers/          # wardrobe, saved_looks, look_image
│   │   └── services/image_generation.py   # provider seam for the next phase
│   ├── tests/test_api.py
│   ├── requirements.txt
│   └── .env.example
└── scripts/                  # PowerShell helpers
```

## Run it locally (Windows PowerShell, e.g. in Cursor)

Prerequisites: **Node.js 20+** and **Python 3.10+** (the `py` launcher ships with the Python installer).

Open the Cursor terminal (`` Ctrl+` ``), make sure it is a **PowerShell** terminal, then use **two terminals** (the `+` / split-terminal button).

### Terminal 1: backend (FastAPI)

```powershell
cd sierrah-fashion-and-beauty\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If PowerShell refuses to run `Activate.ps1`, allow scripts for this terminal only and retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

The API is now at <http://127.0.0.1:8000> (interactive docs at `/docs`, health check at `/health`).

### Terminal 2: frontend (Vite)

```powershell
cd sierrah-fashion-and-beauty\frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Open **<http://localhost:5173>**.

### One-command alternative

From the repo root, this opens both servers in their own windows:

```powershell
.\scripts\start-all.ps1
```

(or run `.\scripts\start-backend.ps1` and `.\scripts\start-frontend.ps1` separately).

### macOS / Linux

```bash
# backend
cd backend && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# frontend (second terminal)
cd frontend && npm install && cp .env.example .env && npm run dev
```

### Other useful commands

```powershell
# Frontend
npm run build        # type-check + production build into frontend\dist
npm run typecheck    # TypeScript only
npm run preview      # serve the production build on :4173

# Backend tests (from backend\, venv active)
python -m pytest -q
```

## Configuration

| File | Variable | Default | Purpose |
|------|----------|---------|---------|
| `frontend/.env` | `VITE_API_BASE_URL` | `http://127.0.0.1:8000` | Where the frontend finds the API |
| `backend/.env` | `DATABASE_PATH` | `data/sierrah.db` | SQLite file (auto-created) |
| `backend/.env` | `CORS_ORIGINS` | `localhost` / `127.0.0.1` on ports 5173 and 4173 | Browser origins allowed to call the API |
| `backend/.env` | `SEED_DEMO_DATA` | `true` | Seed the sample wardrobe on first run |
| `backend/.env` | `IMAGE_PROVIDER` / `IMAGE_API_KEY` / `IMAGE_MODEL` | `none` | Reserved for image generation |

## REST API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/api/wardrobe` | List wardrobe items |
| POST | `/api/wardrobe` | Create an item (idempotent by `id`) |
| PUT | `/api/wardrobe/{id}` | Update an item |
| DELETE | `/api/wardrobe/{id}` | Remove an item |
| PUT | `/api/wardrobe/sync` | Replace the whole wardrobe (**Save Wardrobe**) |
| GET | `/api/saved-looks` | List saved looks |
| POST | `/api/saved-looks` | Save a look (idempotent by `id`) |
| PATCH | `/api/saved-looks/{id}` | Toggle `favorite` |
| DELETE | `/api/saved-looks/{id}` | Delete a saved look |
| PUT | `/api/saved-looks/sync` | Replace all saved looks |
| POST | `/api/look-image` | Image-generation placeholder (see below) |

JSON uses camelCase (`createdAt`, `modelImage`, ...) to match the frontend types.

## How it works

**Offline-first.** The app is fully usable without the backend: the sample wardrobe, saved looks and your preferences live in `localStorage`. When the API is reachable, changes are mirrored to SQLite. If the API is down, a banner appears and changes are flagged so they are pushed up the next time a connection is made, rather than being overwritten.

**Styling engine** (`frontend/src/lib/stylist.ts`). For the chosen occasion, style, colours, traits and notes, each wardrobe item is scored by tags and colour. It picks the best outfit (dress, or top + bottom with sanity rules such as "no kurti with a skirt"), footwear, bag, up to two jewellery pieces, makeup and a hairstyle. If nothing you own fits a slot, it suggests one catalog item within your budget, or a plain-language suggestion if nothing in the catalog fits. A custom occasion is mapped to the nearest profile from keywords like "interview" or "engagement".

**Smart shopping.** An item counts as *missing* only if your wardrobe has nothing tagged as covering it. Delete your sneakers from the wardrobe and "White Sneakers" moves into **Missing Items**.

**Demo prices.** The shopping catalog is sample data. There are no live retailers, links, stock or checkout, and the UI says so. Prices are labelled "Demo price".

**Imagery.** Photography in `frontend/public/images` was AI-generated for this prototype. Model previews are illustrative.

## Next phase: AI image generation

The seam is already in place so nothing in the UI has to change:

1. `frontend/src/services/lookImage.ts` calls `POST /api/look-image` whenever a look is generated.
2. `backend/app/services/image_generation.py` builds a text-to-image prompt from the look (`build_prompt`) and routes to a provider chosen by `IMAGE_PROVIDER`.
3. Add a provider class, register it in `PROVIDERS`, set the three `IMAGE_*` variables, and return `status: "ready"` with an `imageUrl`. The frontend then uses it instead of the curated photo.

## Troubleshooting

- **"Backend not connected" banner:** start the API (Terminal 1) and click **Retry**. The app keeps working and saves locally meanwhile.
- **CORS error in the browser console:** open the app from `http://localhost:5173` or `http://127.0.0.1:5173`, or add your origin to `CORS_ORIGINS` and restart the backend.
- **Port already in use:** change `--port` (backend) and `VITE_API_BASE_URL` to match; for Vite use `npm run dev -- --port 5174` and add that origin to `CORS_ORIGINS`.
- **Start fresh:** Profile → *Reset demo data*, or delete `backend/data/sierrah.db` and clear site data for the app.

## License

[MIT](LICENSE)
