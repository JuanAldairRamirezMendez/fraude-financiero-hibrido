import { useEffect, useRef } from "react";
import { NavLink } from "react-router-dom";

import { Icon } from "@/components/ui/Icon";

import { NAV_ITEMS } from "./navigation";

interface SidebarProps {
  open: boolean;
  onNavigate: () => void;
}

export function Sidebar({ open, onNavigate }: SidebarProps) {
  const navRef = useRef<HTMLElement>(null);

  useEffect(() => {
    if (!open) return;
    navRef.current?.querySelector<HTMLAnchorElement>("a")?.focus();
  }, [open]);

  return (
    <aside id="app-sidebar" className={`sidebar ${open ? "open" : ""}`.trim()}>
      <div className="brand">
        <span className="brand-mark">
          <Icon name="shield" size={21} />
        </span>
        <span>
          Sentinel<span>AI</span>
        </span>
      </div>

      <nav ref={navRef} aria-label="Navegación principal">
        <div className="nav-label">Workspace</div>
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            onClick={onNavigate}
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`.trim()}
          >
            <Icon name={item.icon} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-status">
        <span className="status-dot" aria-hidden="true" />
        <div>
          <strong>Operación conectada</strong>
          <span>API y modelo disponibles</span>
        </div>
      </div>

      <div className="profile">
        <span className="avatar" aria-hidden="true">
          FA
        </span>
        <span>
          <strong>Fraude Analytics</strong>
          <small>Sesión de demostración</small>
        </span>
      </div>
    </aside>
  );
}
