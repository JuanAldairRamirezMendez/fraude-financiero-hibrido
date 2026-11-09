# Frontend — SentinelAI

Interfaz React del sistema híbrido de detección de fraude financiero.

## Stack

- React 19 + TypeScript (strict)
- Vite 8
- Tailwind CSS v4
- TanStack Query (estado de servidor)
- React Router (rutas con lazy loading)
- ESLint + Prettier (calidad y formato)
- Vitest + Testing Library (unitarias y componentes)
- Playwright (E2E)

## Comandos

```bash
# Instalar dependencias (versión fijada en .mise.toml)
npx pnpm@10.34.3 install

# Desarrollo (http://localhost:8443)
npx pnpm@10.34.3 dev

# Verificación de tipos
npx pnpm@10.34.3 typecheck

# Regenerar tipos desde el contrato OpenAPI del backend
npx pnpm@10.34.3 gen:api

# Lint y formato
npx pnpm@10.34.3 lint
npx pnpm@10.34.3 format
npx pnpm@10.34.3 format:check

# Pruebas unitarias y de componentes
npx pnpm@10.34.3 test
npx pnpm@10.34.3 test:coverage

# E2E (la primera vez: npx playwright install chromium)
npx pnpm@10.34.3 e2e

# Verificación completa (lint + typecheck + test + build)
npx pnpm@10.34.3 check

# Build de producción (typecheck + bundle)
npx pnpm@10.34.3 build

# Preview del build
npx pnpm@10.34.3 preview
```

## Calidad

| Herramienta     | Configuración             | Uso                              |
| --------------- | ------------------------- | -------------------------------- |
| ESLint          | `eslint.config.js`        | TypeScript, hooks, a11y, refresh |
| Prettier        | `.prettierrc.json`        | Formato único del proyecto       |
| Vitest          | `vite.config.ts` (`test`) | Unitarias y componentes          |
| Testing Library | `src/test/setup.ts`       | Consultas por rol/label          |
| Playwright      | `playwright.config.ts`    | E2E escritorio + móvil           |

Las pruebas viven junto al código (`*.test.ts(x)`) y los flujos E2E en `e2e/`.
`npm run check` no incluye E2E porque este requiere levantar el servidor y los
navegadores de Playwright; ejecútalo aparte antes de entregar un flujo.

## Configuración

Copia `.env.example` a `.env` y ajusta:

| Variable            | Descripción                                        |
| ------------------- | -------------------------------------------------- |
| `VITE_API_BASE_URL` | URL base de la API (vacío = mismo origen)          |
| `VITE_USE_MOCKS`    | `true` usa datos simulados; `false` consume la API |

No guardes secretos en variables `VITE_*`: son públicas.

## Arquitectura

```text
src/
├── app/            # Router, layout y páginas transversales
├── components/ui/  # Componentes reutilizables sin lógica de negocio
├── features/       # overview, analyzer, models (types, api, hooks, mocks, components)
├── lib/            # Cliente HTTP, CSV, formato
├── config/         # Variables de entorno públicas
├── test/           # Setup de Vitest + Testing Library
└── types/          # Tipos compartidos
e2e/                # Pruebas E2E de Playwright
```

Cada feature sigue el flujo `types → mocks → api → hooks → componentes → página`.
Para conectar el backend real basta con poner `VITE_USE_MOCKS=false` y apuntar
`VITE_API_BASE_URL` a la API; los componentes no cambian.

## Notas

- La sesión debe viajar en cookies `HttpOnly`; el cliente usa `credentials: "include"`.
- Las páginas se cargan con `React.lazy` y cada una genera su propio chunk.
- Los estados de carga, error y vacío están implementados en todas las vistas.
- Las pruebas consultan por rol/label y cubren validación, paginación, búsqueda y
  los estados de las vistas.
