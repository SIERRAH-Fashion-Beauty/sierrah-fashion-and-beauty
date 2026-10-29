import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { Layout } from './components/layout/Layout';
import { EmptyState } from './components/ui/Feedback';
import { HomePage } from './pages/HomePage';
import { LookPage } from './pages/LookPage';
import { OccasionPage } from './pages/OccasionPage';
import { PersonalizePage } from './pages/PersonalizePage';
import { PreviewPage } from './pages/PreviewPage';
import { ProfilePage } from './pages/ProfilePage';
import { SavedLooksPage } from './pages/SavedLooksPage';
import { ShoppingPage } from './pages/ShoppingPage';
import { WardrobePage } from './pages/WardrobePage';

function NotFound() {
  return (
    <EmptyState
      title="Page not found"
      message="That page doesn't exist, but your perfect look is just a click away."
      action={
        <Link to="/" className="btn-primary">
          Back to home
        </Link>
      }
    />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="wardrobe" element={<WardrobePage />} />
            <Route path="style" element={<OccasionPage />} />
            <Route path="personalize" element={<PersonalizePage />} />
            <Route path="look" element={<LookPage />} />
            <Route path="preview" element={<PreviewPage />} />
            <Route path="shopping" element={<ShoppingPage />} />
            <Route path="saved" element={<SavedLooksPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </AppProvider>
    </BrowserRouter>
  );
}
