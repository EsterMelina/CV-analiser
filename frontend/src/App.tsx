import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { Layout } from "@/components/Layout";
import { LoginPage } from "@/pages/LoginPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { JobsListPage } from "@/pages/JobsListPage";
import { JobCreatePage } from "@/pages/JobCreatePage";
import { JobDetailPage } from "@/pages/JobDetailPage";
import { CandidateOverview } from "@/pages/CandidateOverview";
import { EmailSettingsPage } from "@/pages/EmailSettingsPage";
import { QuestionnairePrintPage } from "@/pages/QuestionnairePrintPage";

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/questionnaires/:versionId/print" element={<QuestionnairePrintPage />} />
            <Route element={<Layout />}>
              <Route path="/" element={<DashboardPage />} />
              <Route path="/jobs" element={<JobsListPage />} />
              <Route path="/jobs/new" element={<JobCreatePage />} />
              <Route path="/jobs/:jobId" element={<JobDetailPage />} />
              <Route path="/jobs/:jobId/applications/:applicationId" element={<CandidateOverview />} />
              <Route path="/settings/email" element={<EmailSettingsPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
