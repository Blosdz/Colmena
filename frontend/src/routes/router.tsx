import { createBrowserRouter, Navigate, useParams } from "react-router-dom";

import App from "../App";
import { ArchiveFormsPage } from "../pages/ArchiveFormsPage";
import { ArchiveProjectsPage } from "../pages/ArchiveProjectsPage";
import { StartPage } from "../pages/StartPage";
import { NotFoundPage } from "../pages/NotFoundPage";
import { SettingsPage } from "../pages/SettingsPage";
import { ProjectResultsPage } from "../pages/ProjectResultsPage";
import { ProjectCreateWizard } from "../pages/ProjectCreateWizard";
import { ProjectReportsPage } from "../pages/ProjectReportsPage";
import { ProjectLinkResponsesPage } from "../pages/ProjectLinkResponsesPage";
import { ProjectFormDesigner } from "../pages/ProjectFormDesigner";
import { ProjectTelemetryPage } from "../pages/ProjectTelemetryPage";
import { PublicFormPage } from "../pages/PublicFormPage";

function StudyToProjectRedirect({ mode }: { mode: "workspace" | "builder" | "form" | "publish" | "responses" | "analysis" | "presentation" }) {
  const { projectId = "" } = useParams();
  const mapping = {
    workspace: `/project/${projectId}`,
    builder: `/project/${projectId}`,
    form: `/project/${projectId}/form`,
    publish: `/project/${projectId}/link`,
    responses: `/project/${projectId}/telemetry`,
    analysis: `/project/${projectId}/results`,
    presentation: `/project/${projectId}/reports`,
  } as const;
  return <Navigate replace to={mapping[mode]} />;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: <StartPage /> },
      { path: "project/new", element: <ProjectCreateWizard /> },
      { path: "project/:projectId", element: <ProjectCreateWizard /> },
      { path: "project/:projectId/form", element: <ProjectFormDesigner /> },
      { path: "project/:projectId/link", element: <ProjectLinkResponsesPage /> },
      { path: "project/:projectId/telemetry", element: <ProjectTelemetryPage /> },
      { path: "project/:projectId/results", element: <ProjectResultsPage /> },
      { path: "project/:projectId/reports", element: <ProjectReportsPage /> },
      { path: "study/new", element: <Navigate replace to="/project/new" /> },
      { path: "study/:projectId/workspace", element: <StudyToProjectRedirect mode="workspace" /> },
      { path: "study/:projectId/builder", element: <StudyToProjectRedirect mode="builder" /> },
      { path: "study/:projectId/form", element: <StudyToProjectRedirect mode="form" /> },
      { path: "study/:projectId/publish", element: <StudyToProjectRedirect mode="publish" /> },
      { path: "study/:projectId/responses", element: <StudyToProjectRedirect mode="responses" /> },
      { path: "study/:projectId/analysis", element: <StudyToProjectRedirect mode="analysis" /> },
      { path: "study/:projectId/presentation", element: <StudyToProjectRedirect mode="presentation" /> },
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

