import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AuthProvider } from '@/features/auth/AuthProvider';
import { ProtectedRoute } from '@/features/auth/ProtectedRoute';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { AppLayout } from '@/components/layout/AppLayout';
import { DashboardPage } from '@/pages/DashboardPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { ForbiddenPage } from '@/pages/ForbiddenPage';
import { ElevesPage } from '@/features/eleves/pages/ElevesPage';
import { EleveDetailPage } from '@/features/eleves/pages/EleveDetailPage';
import { EleveCreatePage } from '@/features/eleves/pages/EleveCreatePage';
import { EleveEditPage } from '@/features/eleves/pages/EleveEditPage';
import { FamillesListPage } from '@/features/familles/pages/FamillesListPage';
import { FamilleCreatePage } from '@/features/familles/pages/FamilleCreatePage';
import { FamilleDetailPage } from '@/features/familles/pages/FamilleDetailPage';
import { FamilleEditPage } from '@/features/familles/pages/FamilleEditPage';
import { InscriptionCreatePage } from '@/features/inscriptions/pages/InscriptionCreatePage';
import { InscriptionDetailPage } from '@/features/inscriptions/pages/InscriptionDetailPage';
import { InscriptionEditPage } from '@/features/inscriptions/pages/InscriptionEditPage';
import { EleveSituationPage } from '@/features/situation/pages/EleveSituationPage';
import { PaiementsListPage } from '@/features/paiements/pages/PaiementsListPage';
import { PaiementCreatePage } from '@/features/paiements/pages/PaiementCreatePage';
import { ChargesListPage } from '@/features/charges/pages/ChargesListPage';
import { ChargeCreatePage } from '@/features/charges/pages/ChargeCreatePage';
import { SalairesPage } from '@/features/salaires/pages/SalairesPage';
import { AssociesListPage } from '@/features/associes/pages/AssociesListPage';
import { PrelevementsListPage } from '@/features/prelevements/pages/PrelevementsListPage';
import { PrelevementCreatePage } from '@/features/prelevements/pages/PrelevementCreatePage';
import { CaisseFgListPage } from '@/features/caisse_fg/pages/CaisseFgListPage';
import { CaisseFgCreatePage } from '@/features/caisse_fg/pages/CaisseFgCreatePage';

const DevUiPage = import.meta.env.DEV
  ? lazy(() => import('@/pages/DevUiPage').then((m) => ({ default: m.DevUiPage })))
  : null;

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/403" element={<ForbiddenPage />} />

        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route index element={<DashboardPage />} />

            {/* Élèves */}
            <Route element={<ProtectedRoute resource="eleves" action="read" />}>
              <Route path="/eleves" element={<ElevesPage />} />
              <Route path="/eleves/:id" element={<EleveDetailPage />} />
              <Route path="/eleves/:id/situation" element={<EleveSituationPage />} />
            </Route>
            <Route element={<ProtectedRoute resource="eleves" action="create" />}>
              <Route path="/eleves/nouveau" element={<EleveCreatePage />} />
            </Route>
            <Route element={<ProtectedRoute resource="eleves" action="update" />}>
              <Route path="/eleves/:id/modifier" element={<EleveEditPage />} />
            </Route>

            {/* Familles */}
            <Route element={<ProtectedRoute resource="familles" action="read" />}>
              <Route path="/familles" element={<FamillesListPage />} />
              <Route path="/familles/:id" element={<FamilleDetailPage />} />
            </Route>
            <Route element={<ProtectedRoute resource="familles" action="create" />}>
              <Route path="/familles/nouvelle" element={<FamilleCreatePage />} />
            </Route>
            <Route element={<ProtectedRoute resource="familles" action="update" />}>
              <Route path="/familles/:id/modifier" element={<FamilleEditPage />} />
            </Route>

            {/* Inscriptions */}
            <Route element={<ProtectedRoute resource="inscriptions" action="read" />}>
              <Route path="/inscriptions/:id" element={<InscriptionDetailPage />} />
            </Route>
            <Route element={<ProtectedRoute resource="inscriptions" action="create" />}>
              <Route path="/eleves/:id/inscrire" element={<InscriptionCreatePage />} />
            </Route>
            <Route element={<ProtectedRoute resource="inscriptions" action="update" />}>
              <Route path="/inscriptions/:id/modifier" element={<InscriptionEditPage />} />
            </Route>

            {/* Paiements */}
            <Route element={<ProtectedRoute resource="paiements" action="read" />}>
              <Route path="/paiements" element={<PaiementsListPage />} />
            </Route>
            <Route element={<ProtectedRoute resource="paiements" action="create" />}>
              <Route path="/paiements/nouveau" element={<PaiementCreatePage />} />
            </Route>

            {/* Charges */}
            <Route element={<ProtectedRoute resource="charges" action="read" />}>
              <Route path="/charges" element={<ChargesListPage />} />
            </Route>
            <Route element={<ProtectedRoute resource="charges" action="create" />}>
              <Route path="/charges/nouvelle" element={<ChargeCreatePage />} />
            </Route>

            {/* Salaires */}
            <Route element={<ProtectedRoute resource="salaires_mensuels" action="read" />}>
              <Route path="/salaires" element={<SalairesPage />} />
            </Route>

            {/* Associés */}
            <Route element={<ProtectedRoute resource="associes" action="read" />}>
              <Route path="/associes" element={<AssociesListPage />} />
            </Route>

            {/* Prélèvements */}
            <Route element={<ProtectedRoute resource="prelevements" action="read" />}>
              <Route path="/prelevements" element={<PrelevementsListPage />} />
            </Route>
            <Route element={<ProtectedRoute resource="prelevements" action="create" />}>
              <Route path="/prelevements/nouveau" element={<PrelevementCreatePage />} />
            </Route>
            {/* Caisse FG */}
            <Route element={<ProtectedRoute resource="caisse_fg" action="read" />}>
              <Route path="/caisse-fg" element={<CaisseFgListPage />} />
            </Route>
            <Route element={<ProtectedRoute resource="caisse_fg" action="create" />}>
              <Route path="/caisse-fg/nouveau" element={<CaisseFgCreatePage />} />
            </Route>

            {DevUiPage && (
              <Route
                path="/dev/ui"
                element={
                  <Suspense fallback={<div className="p-6 text-sm text-muted-foreground">Chargement…</div>}>
                    <DevUiPage />
                  </Suspense>
                }
              />
            )}
          </Route>
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Routes>
      <Toaster richColors position="top-right" />
    </AuthProvider>
  );
}