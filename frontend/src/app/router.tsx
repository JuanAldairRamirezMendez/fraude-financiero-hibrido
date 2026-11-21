import { lazy, Suspense, type ReactNode } from "react";
import { createBrowserRouter } from "react-router-dom";

import { PageSkeleton } from "@/components/ui/PageState";
import { CasesPage } from "@/features/cases/CasesPage";
import { ChatPage } from "@/features/chat/ChatPage";

import { AuthProvider, ProtectedRoute } from "./auth/AuthContext";
import { AppLayout } from "./layout/AppLayout";
import { LoginPage } from "./pages/LoginPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { RouteErrorPage } from "./pages/RouteErrorPage";

const OverviewPage = lazy(() => import("@/features/overview/OverviewPage"));
const AnalyzerPage = lazy(() => import("@/features/analyzer/AnalyzerPage"));
const BenchmarkPage = lazy(() => import("@/features/benchmark/BenchmarkPage"));
const EvaluationPage = lazy(() => import("@/features/evaluation/EvaluationPage"));

function withSuspense(node: ReactNode) {
  return <Suspense fallback={<PageSkeleton />}>{node}</Suspense>;
}

export const router = createBrowserRouter([
  {
    element: <AuthProvider />,
    errorElement: <RouteErrorPage />,
    children: [
      { path: "login", element: <LoginPage /> },
      {
        path: "/",
        element: <ProtectedRoute><AppLayout /></ProtectedRoute>,
        children: [
          { index: true, element: withSuspense(<OverviewPage />) },
          { path: "evaluation", element: withSuspense(<EvaluationPage />) },
          { path: "analyzer", element: withSuspense(<AnalyzerPage />) },
          { path: "benchmark", element: withSuspense(<BenchmarkPage />) },
          { path: "cases", element: withSuspense(<CasesPage />) },
          { path: "chat", element: withSuspense(<ChatPage />) },
          { path: "*", element: <NotFoundPage /> },
        ],
      },
    ],
  },
]);
