const rawApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim() ?? "";

/**
 * Configuración pública del frontend.
 * Solo variables VITE_* (públicas). Nunca secretos.
 */
export const env = {
  apiBaseUrl: `${rawApiBaseUrl.replace(/\/$/, "")}/api/v1`,
  useMocks: import.meta.env.VITE_USE_MOCKS !== "false",
} as const;
