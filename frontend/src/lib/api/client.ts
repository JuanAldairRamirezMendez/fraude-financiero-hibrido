import { env } from "@/config/env";

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly requestId?: string;

  constructor(message: string, status: number, code?: string, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

type RequestOptions = Omit<RequestInit, "body"> & { body?: unknown };

/**
 * Cliente HTTP único del frontend.
 * - `credentials: "include"` para que la sesión viaje en cookies HttpOnly.
 * - No guarda tokens ni secretos en el navegador.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, headers, ...rest } = options;

  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as {
      code?: string;
      message?: string;
      requestId?: string;
    } | null;
    throw new ApiError(
      body?.message ?? "No se pudo completar la solicitud.",
      response.status,
      body?.code,
      body?.requestId ?? response.headers.get("X-Request-ID") ?? undefined,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
