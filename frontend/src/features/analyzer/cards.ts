import { GENDER_LABELS } from "@/lib/labels";

import raw from "./cards.json";

/**
 * Catálogo de tarjetas del dataset Sparkov, generado por
 * `backend/scripts/build_sparkov_artifacts.py`. Los números de tarjeta reales no se
 * guardan: cada una tiene un alias (`TARJ-0001`). El historial de compras de cada
 * tarjeta vive en el backend.
 */
export interface CardInfo {
  id: string;
  gender: string;
  birthYear: number;
  city: string;
  state: string;
}

export const CARDS: readonly CardInfo[] = raw as CardInfo[];

export const CARD_IDS: ReadonlySet<string> = new Set(CARDS.map((card) => card.id));

const BY_ID = new Map(CARDS.map((card) => [card.id, card]));

export function cardInfo(id: string): CardInfo | undefined {
  return BY_ID.get(id);
}

/** "TARJ-0471 · Mujer, 1968 · Houston, TX" */
export function cardLabel(card: CardInfo): string {
  return `${card.id} · ${GENDER_LABELS[card.gender] ?? card.gender}, ${card.birthYear} · ${card.city}, ${card.state}`;
}

export const CARD_LABELS: Readonly<Record<string, string>> = Object.fromEntries(
  CARDS.map((card) => [card.id, cardLabel(card)]),
);
