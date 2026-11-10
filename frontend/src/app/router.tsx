import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter } from "react-router-dom";

import { PageSkeleton } from "@/components/ui/PageState";
import { ChatPage } from "@/features/chat/ChatPage";

import { AppLayout } from "./layout/AppLayout";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RouteErrorPage } from "./pages/RouteErrorPage";
import { ReportsPage } from "./pages/ReportsPage";
import { SettingsPage } from "./pages/SettingsPage";

const OverviewPage = lazy(() => import("@/features/overview/OverviewPage"));
const AnalyzerPage = lazy(() => import("@/features/analyzer/AnalyzerPage"));
const ModelsPage = lazy(() => import("@/features/models/ModelsPage"));

function withSuspense(node: ReactNode) {
  return <Suspense fallback={<PageSkeleton />}>{node}</Suspense>;
}

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: withSuspense(<OverviewPage />) },
      { path: "analyzer", element: withSuspense(<AnalyzerPage />) },
      { path: "models", element: withSuspense(<ModelsPage />) },
      { path: "chat", element: withSuspense(<ChatPage />) },
      { path: "reports", element: <ReportsPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
