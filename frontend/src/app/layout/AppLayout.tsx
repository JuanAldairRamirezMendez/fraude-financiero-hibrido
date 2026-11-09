import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { AppHeader } from "./AppHeader";
import { DEFAULT_ROUTE_META, ROUTE_META } from "./navigation";
import { Sidebar } from "./Sidebar";

export function AppLayout() {
  const { pathname } = useLocation();
  const menuButtonRef = useRef<HTMLButtonElement>(null);
  const [openPath, setOpenPath] = useState<string | null>(null);
  const sidebarOpen = openPath === pathname;
  const meta = ROUTE_META[pathname] ?? DEFAULT_ROUTE_META;

  function closeSidebar() {
    setOpenPath(null);
    menuButtonRef.current?.focus();
  }

  useEffect(() => {
    if (!sidebarOpen) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpenPath(null);
        menuButtonRef.current?.focus();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [sidebarOpen]);

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Saltar al contenido principal
      </a>

      <Sidebar open={sidebarOpen} onNavigate={closeSidebar} />

      {sidebarOpen && (
        <button
          type="button"
          className="sidebar-backdrop"
          aria-label="Cerrar menú de navegación"
          onClick={closeSidebar}
        />
      )}

      <div className="workspace">
        <AppHeader
          title={meta.title}
          eyebrow={meta.eyebrow}
          menuOpen={sidebarOpen}
          menuButtonRef={menuButtonRef}
          onToggleMenu={() => setOpenPath((current) => (current === pathname ? null : pathname))}
        />
        <main id="main-content" className="page-content" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
