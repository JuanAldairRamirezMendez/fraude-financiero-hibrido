import { useState, type FormEvent, type RefObject } from "react";
import { NavLink, useNavigate } from "react-router-dom";

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
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const term = query.trim();
    navigate(term ? `/?q=${encodeURIComponent(term)}` : "/");
  }

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
        <form className="search" role="search" onSubmit={handleSearch}>
          <Icon name="search" size={17} />
          <label className="sr-only" htmlFor="global-search">
            Buscar transacciones por ID o cliente
          </label>
          <input
            id="global-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Buscar transacciones..."
          />
        </form>
        <NavLink className="icon-button" to="/models" aria-label="Ver alertas del modelo">
          <Icon name="bell" size={19} />
          <span className="notification-dot" aria-hidden="true" />
        </NavLink>
        <div className="live-pill">
          <span aria-hidden="true" />
          Live monitoring
        </div>
      </div>
    </header>
  );
}
