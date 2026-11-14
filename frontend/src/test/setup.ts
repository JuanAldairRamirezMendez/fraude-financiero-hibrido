import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

import { resetAnalyzerSession } from "@/features/analyzer/session";

// Sin globals de Vitest, Testing Library no registra su limpieza automática.
afterEach(() => {
  cleanup();
  // El estado del Analizador vive fuera de React: se reinicia para aislar cada test.
  resetAnalyzerSession();
});
