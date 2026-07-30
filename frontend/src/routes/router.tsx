import { createBrowserRouter, Navigate, useParams } from "react-router-dom";

import App from "../App";
import { ArchiveFormsPage } from "../pages/ArchiveFormsPage";
import { ArchiveProjectsPage } from "../pages/ArchiveProjectsPage";
import { StartPage } from "../pages/StartPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { SettingsPage } from "../pages/SettingsPage";
import { ProjectCreateWizard } from "../pages/ProjectCreateWizard";
import { ProjectLinkResponsesPage } from "../pages/ProjectLinkResponsesPage";
import { ProjectFormDesigner } from "../pages/ProjectFormDesigner";
import { ProjectTelemetryPage } from "../pages/ProjectTelemetryPage";
import { PublicFormPage } from "../pages/PublicFormPage";
import { LoginPage } from "../pages/LoginPage";
import { AuthCallbackPage } from "../pages/AuthCallbackPage";
import { RequireAuth } from "../auth/RequireAuth";

function StudyToProjectRedirect({ mode }: { mode: "workspace" | "builder" | "form" | "publish" | "responses" }) {
  const { projectId = "" } = useParams();
  const mapping = {
    workspace: `/project/${projectId}`,
    builder: `/project/${projectId}`,
    form: `/project/${projectId}/form`,
    publish: `/project/${projectId}/link`,
    responses: `/project/${projectId}/telemetry`,
  } as const;
  return <Navigate replace to={mapping[mode]} />;
}

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/auth/callback",
    element: <AuthCallbackPage />,
  },
  {
    path: "/",
    element: (
      <RequireAuth>
        <App />
      </RequireAuth>
    ),
    children: [
      { index: true, element: <StartPage /> },
      { path: "project/new", element: <ProjectCreateWizard /> },
      { path: "project/:projectId", element: <ProjectCreateWizard /> },
      { path: "project/:projectId/form", element: <ProjectFormDesigner /> },
      { path: "project/:projectId/link", element: <ProjectLinkResponsesPage /> },
      { path: "project/:projectId/telemetry", element: <ProjectTelemetryPage /> },
      { path: "study/new", element: <Navigate replace to="/project/new" /> },
      { path: "study/:projectId/workspace", element: <StudyToProjectRedirect mode="workspace" /> },
      { path: "study/:projectId/builder", element: <StudyToProjectRedirect mode="builder" /> },
      { path: "study/:projectId/form", element: <StudyToProjectRedirect mode="form" /> },
      { path: "study/:projectId/publish", element: <StudyToProjectRedirect mode="publish" /> },
      { path: "study/:projectId/responses", element: <StudyToProjectRedirect mode="responses" /> },
      { path: "archive/projects", element: <ArchiveProjectsPage /> },
      { path: "archive/forms", element: <ArchiveFormsPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
  {
    path: "public/forms/:publicSlug",
    element: <PublicFormPage />,
  },
]);

