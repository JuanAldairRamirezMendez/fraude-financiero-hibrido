import type { RefObject } from "react";
import { NavLink } from "react-router-dom";

import { Icon } from "@/components/ui/Icon";

interface AppHeaderProps {
  title: string;
  eyebrow: string;
  menuOpen: boolean;
  menuButtonRef: RefObject<HTMLButtonElement | null>;
  onToggleMenu: () => void;
}

export function AppHeader({
  title,
  eyebrow,
  menuOpen,
  menuButtonRef,
  onToggleMenu,
}: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="header-title">
        <button
          ref={menuButtonRef}
          type="button"
          className="menu-button"
          onClick={onToggleMenu}
          aria-expanded={menuOpen}
          aria-controls="app-sidebar"
          aria-label={menuOpen ? "Cerrar menú de navegación" : "Abrir menú de navegación"}
        >
          <Icon name={menuOpen ? "close" : "menu"} size={20} />
        </button>
        <div>
          <p className="eyebrow">{eyebrow}</p>
          <h1 className="page-title">{title}</h1>
        </div>
      </div>

      <div className="header-actions">
        <NavLink className="icon-button" to="/cases" aria-label="Ver casos pendientes de revisión">
          <Icon name="bell" size={19} />
        </NavLink>
      </div>
    </header>
  );
}
