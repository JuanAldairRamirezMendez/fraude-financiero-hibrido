import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";

import { env } from "@/config/env";
import { apiRequest, ApiError } from "@/lib/api/client";

interface AuthUser {
  id: string;
  username: string;
  role: "admin" | "analyst" | "viewer";
}

interface AuthResponse {
  user: AuthUser;
  expires_in: number;
}

interface AuthStatusResponse {
  authenticated: boolean;
  user?: AuthUser | null;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children?: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (env.useMocks) {
      setIsLoading(false);
      return;
    }

    let active = true;

    apiRequest<AuthStatusResponse>("/auth/me")
      .then((status) => {
        if (active) setUser(status.authenticated ? status.user ?? null : null);
      })
      .catch((error: unknown) => {
        if (active && (!(error instanceof ApiError) || error.status !== 401)) setUser(null);
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  async function login(username: string, password: string) {
    const response = await apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: { username, password },
    });
    setUser(response.user);
  }

  async function logout() {
    if (env.useMocks) {
      setUser(null);
      return;
    }

    const csrfToken = document.cookie
      .split("; ")
      .find((cookie) => cookie.startsWith("csrf_token="))
      ?.split("=")[1];

    await apiRequest<void>("/auth/logout", {
      method: "POST",
      headers: csrfToken ? { "X-CSRF-Token": decodeURIComponent(csrfToken) } : undefined,
    });
    setUser(null);
  }

  const value = useMemo(
    () => ({ user, isLoading, isAuthenticated: user !== null, login, logout }),
    [user, isLoading],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
      <Outlet />
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return context;
}

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isLoading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (env.useMocks) return children;
  if (isLoading) return <div className="page-state" role="status">Comprobando sesión...</div>;
  if (!isAuthenticated) {
    return <NavigateToLogin state={{ from: location.pathname }} />;
  }
  return children;
}

function NavigateToLogin({ state }: { state: { from: string } }) {
  const navigate = useNavigate();
  useEffect(() => {
    navigate("/login", { replace: true, state });
  }, [navigate, state]);
  return <div className="page-state" role="status">Redirigiendo al inicio de sesión...</div>;
}