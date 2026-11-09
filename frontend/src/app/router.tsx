import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter } from "react-router-dom";

import { PageSkeleton } from "@/components/ui/PageState";

import { AppLayout } from "./layout/AppLayout";
import { ComingSoonPage } from "./pages/ComingSoonPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RouteErrorPage } from "./pages/RouteErrorPage";

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
      {
        path: "reports",
        element: (
          <ComingSoonPage
            title="Reports"
            description="La exportación de reportes analíticos se conectará al backend en la siguiente fase."
          />
        ),
      },
      {
        path: "settings",
        element: (
          <ComingSoonPage
            title="Settings"
            description="La configuración de umbrales y modelos estará disponible al integrar la API."
          />
        ),
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
