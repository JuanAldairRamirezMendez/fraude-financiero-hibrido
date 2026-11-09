import type { IconName } from "@/components/ui/Icon";

export interface NavItem {
  to: string;
  label: string;
  icon: IconName;
  end?: boolean;
}

export const NAV_ITEMS: ReadonlyArray<NavItem> = [
  { to: "/", label: "Overview", icon: "grid", end: true },
  { to: "/analyzer", label: "Analyzer", icon: "alert" },
  { to: "/models", label: "Models", icon: "model" },
  { to: "/reports", label: "Reports", icon: "report" },
  { to: "/settings", label: "Settings", icon: "settings" },
];

interface RouteMeta {
  eyebrow: string;
  title: string;
}

export const ROUTE_META: Record<string, RouteMeta> = {
  "/": { eyebrow: "Command center", title: "Overview" },
  "/analyzer": { eyebrow: "Real-time decisioning", title: "Transaction Analyzer" },
  "/models": { eyebrow: "Monitoring & governance", title: "Model Health" },
  "/reports": { eyebrow: "Analytics", title: "Reports" },
  "/settings": { eyebrow: "Administration", title: "Settings" },
};

export const DEFAULT_ROUTE_META: RouteMeta = {
  eyebrow: "Fraud operations",
  title: "SentinelAI",
};
