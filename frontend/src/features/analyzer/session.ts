import { useCallback, useSyncExternalStore } from "react";

import type { RealSample } from "./realSamples";
import type { RiskAssessment } from "./types";
import { INITIAL_FORM_VALUES, type TransactionFormValues } from "./validation";

/**
 * Estado del Analizador que sobrevive al cambiar de página (por ejemplo, al abrir el caso en
 * Revisión de casos y volver). Vive fuera de React y se copia en sessionStorage, así que también
 * resiste una recarga de la pestaña; se borra al cerrar sesión.
 */
export interface AnalyzerSession {
  values: TransactionFormValues;
  activeScenario: string | null;
  /** Muestra real cargada en el formulario (aún sin analizar). */
  realSample: RealSample | null;
  /** Último resultado y la muestra real con la que se obtuvo, si la hubo. */
  result: RiskAssessment | null;
  analyzedSample: RealSample | null;
}

const STORAGE_KEY = "sentinelai.analyzer";

const EMPTY: AnalyzerSession = {
  values: INITIAL_FORM_VALUES,
  activeScenario: null,
  realSample: null,
  result: null,
  analyzedSample: null,
};

function load(): AnalyzerSession {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY;
    const stored = JSON.parse(raw) as Partial<AnalyzerSession>;
    // Los campos nuevos del formulario toman su valor inicial si no estaban guardados.
    return { ...EMPTY, ...stored, values: { ...INITIAL_FORM_VALUES, ...stored.values } };
  } catch {
    return EMPTY;
  }
}

let state: AnalyzerSession = load();
const listeners = new Set<() => void>();

function emit(next: AnalyzerSession) {
  state = next;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // Sin almacenamiento (modo privado, etc.) el estado sigue en memoria mientras dure la pestaña.
  }
  listeners.forEach((listener) => listener());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function updateAnalyzerSession(changes: Partial<AnalyzerSession>) {
  emit({ ...state, ...changes });
}

export function resetAnalyzerSession() {
  state = EMPTY;
  try {
    sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nada que limpiar.
  }
  listeners.forEach((listener) => listener());
}

type Updater<T> = T | ((previous: T) => T);

/** Igual que `useState`, pero el valor se conserva entre visitas al Analizador. */
export function useAnalyzerSession<K extends keyof AnalyzerSession>(
  key: K,
): [AnalyzerSession[K], (value: Updater<AnalyzerSession[K]>) => void] {
  const value = useSyncExternalStore(subscribe, () => state[key]);
  const setValue = useCallback(
    (next: Updater<AnalyzerSession[K]>) => {
      const resolved =
        typeof next === "function"
          ? (next as (previous: AnalyzerSession[K]) => AnalyzerSession[K])(state[key])
          : next;
      emit({ ...state, [key]: resolved });
    },
    [key],
  );
  return [value, setValue];
}
