import type { IconName } from "@/components/ui/Icon";

export interface NavItem {
  to: string;
  label: string;
  icon: IconName;
  end?: boolean;
  /** Muestra el número de casos pendientes junto a la etiqueta. */
  showPendingCases?: boolean;
}

export const NAV_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/", label: "Resumen", icon: "grid", end: true },
  { to: "/evaluation", label: "Evaluación", icon: "report" },
  { to: "/benchmark", label: "Comparativa IA", icon: "target" },
  { to: "/analyzer", label: "Analizador", icon: "activity" },
  { to: "/cases", label: "Revisión de casos", icon: "alert", showPendingCases: true },
  { to: "/models", label: "Salud del modelo", icon: "model" },
  { to: "/chat", label: "Copiloto IA", icon: "message" },
];

interface RouteMeta {
  eyebrow: string;
  title: string;
}

export const ROUTE_META: Record<string, RouteMeta> = {
  "/": { eyebrow: "Centro de mando", title: "Resumen" },
  "/evaluation": { eyebrow: "Prueba con datos no vistos", title: "Evaluación del modelo" },
  "/analyzer": { eyebrow: "Decisión en tiempo real", title: "Analizador de transacciones" },
  "/benchmark": { eyebrow: "IA híbrida · CRISP-DM", title: "Comparativa de modelos" },
  "/cases": { eyebrow: "Humano en el circuito", title: "Revisión de casos" },
  "/models": { eyebrow: "Monitoreo y gobierno", title: "Salud del modelo" },
  "/chat": { eyebrow: "Asistente inteligente", title: "Copiloto IA" },
};

export const DEFAULT_ROUTE_META: RouteMeta = {
  eyebrow: "Operaciones antifraude",
  title: "SentinelAI",
};
