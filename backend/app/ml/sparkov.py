"""Variables del modelo de fraude entrenado con el dataset Sparkov.

Una sola fuente de verdad para el entrenamiento (``batch_features``, vectorizado
sobre todo el dataset) y para la API (``CardHistory.features_for``, una
transacción en vivo). Ambas calculan exactamente las mismas columnas en el
mismo orden; ``tests/unit/test_sparkov_features.py`` lo verifica.

Las variables de historial solo usan transacciones ANTERIORES de la misma
tarjeta y nunca la etiqueta de fraude.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd

CATEGORIES: tuple[str, ...] = (
    "entertainment",
    "food_dining",
    "gas_transport",
    "grocery_net",
    "grocery_pos",
    "health_fitness",
    "home",
    "kids_pets",
    "misc_net",
    "misc_pos",
    "personal_care",
    "shopping_net",
    "shopping_pos",
    "travel",
)
NIGHT_HOURS = (22, 23, 0, 1, 2, 3)
NO_PREVIOUS_SECONDS = 1e7
WINDOWS: tuple[tuple[str, int], ...] = (("1h", 3_600), ("24h", 86_400), ("7d", 604_800))

TRANSACTION_FEATURES: tuple[str, ...] = (
    "monto",
    "log_monto",
    "hora",
    "dia_semana",
    "nocturna",
    "edad",
    "genero_m",
    "log_poblacion",
    "distancia_km",
    "monto_vs_categoria",
    *(f"cat_{category}" for category in CATEGORIES),
)
HISTORY_FEATURES: tuple[str, ...] = (
    "compras_previas",
    "seg_desde_anterior",
    "monto_vs_promedio_tarjeta",
    "monto_z_tarjeta",
    "misma_categoria_previas",
    "compras_1h",
    "monto_1h",
    "compras_24h",
    "monto_24h",
    "compras_7d",
    "monto_7d",
    "monto_vs_24h",
)
FEATURE_NAMES: tuple[str, ...] = TRANSACTION_FEATURES + HISTORY_FEATURES


def channel_of(category: str) -> str:
    """Canal derivado del nombre de la categoría: *_net en línea, *_pos presencial."""
    if category.endswith("_net"):
        return "online"
    if category.endswith("_pos"):
        return "pos"
    return "other"


def haversine_km(lat1, lon1, lat2, lon2):  # type: ignore[no-untyped-def]
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


def _transaction_features(
    amount: np.ndarray,
    ts: pd.Series,
    dob: pd.Series,
    gender_male: np.ndarray,
    city_pop: np.ndarray,
    distance_km: np.ndarray,
    category: pd.Series,
    category_medians: dict[str, float],
) -> pd.DataFrame:
    out = pd.DataFrame(index=category.index)
    out["monto"] = amount
    out["log_monto"] = np.log1p(amount)
    out["hora"] = ts.dt.hour.to_numpy()
    out["dia_semana"] = ts.dt.day_of_week.to_numpy()
    out["nocturna"] = ts.dt.hour.isin(NIGHT_HOURS).astype(int).to_numpy()
    out["edad"] = ((ts - dob).dt.days / 365.25).to_numpy()
    out["genero_m"] = gender_male
    out["log_poblacion"] = np.log1p(city_pop)
    out["distancia_km"] = distance_km
    medians = category.map(category_medians).astype(float).to_numpy()
    out["monto_vs_categoria"] = amount / (medians + 1)
    for name in CATEGORIES:
        out[f"cat_{name}"] = (category == name).astype(int).to_numpy()
    return out


def batch_features(df: pd.DataFrame, category_medians: dict[str, float]) -> pd.DataFrame:
    """Variables para todo un DataFrame con las columnas del dataset Sparkov.

    Requiere: ``card_id``, ``ts`` (datetime), ``amt``, ``category``, ``gender``,
    ``dob`` (datetime), ``city_pop`` y ``distancia_km``.
    """

    out = _transaction_features(
        df["amt"].to_numpy(dtype=float),
        df["ts"],
        df["dob"],
        (df["gender"] == "M").astype(int).to_numpy(),
        df["city_pop"].to_numpy(dtype=float),
        df["distancia_km"].to_numpy(dtype=float),
        df["category"],
        category_medians,
    )

    order = np.lexsort((df["ts"].to_numpy(), df["card_id"].to_numpy()))
    s = pd.DataFrame(
        {
            "card": df["card_id"].to_numpy()[order],
            "ts": df["ts"].to_numpy()[order],
            "amt": df["amt"].to_numpy(dtype=float)[order],
            "cat": df["category"].to_numpy()[order],
        }
    )
    g = s.groupby("card", sort=False)
    hist = pd.DataFrame(index=s.index)
    previous = g.cumcount().astype(float)
    hist["compras_previas"] = previous
    hist["seg_desde_anterior"] = g["ts"].diff().dt.total_seconds().fillna(NO_PREVIOUS_SECONDS)
    prev_sum = g["amt"].cumsum() - s["amt"]
    prev_sq = (s["amt"] ** 2).groupby(s["card"], sort=False).cumsum() - s["amt"] ** 2
    has_previous = previous.replace(0, np.nan)
    prev_mean = prev_sum / has_previous
    prev_std = np.sqrt((prev_sq / has_previous - prev_mean**2).clip(lower=0))
    hist["monto_vs_promedio_tarjeta"] = (s["amt"] / (prev_mean + 1)).fillna(1.0)
    hist["monto_z_tarjeta"] = ((s["amt"] - prev_mean) / (prev_std + 1)).fillna(0.0)
    hist["misma_categoria_previas"] = s.groupby(["card", "cat"], sort=False).cumcount().astype(float)
    indexed = s.set_index("ts")
    for name, seconds in WINDOWS:
        rolled = indexed.groupby("card", sort=False)["amt"].rolling(pd.Timedelta(seconds=seconds))
        hist[f"compras_{name}"] = rolled.count().to_numpy()
        hist[f"monto_{name}"] = rolled.sum().to_numpy()
    hist["monto_vs_24h"] = s["amt"] / (hist["monto_24h"] + 1)

    restored = np.empty((len(df), len(HISTORY_FEATURES)))
    restored[order] = hist[list(HISTORY_FEATURES)].to_numpy(dtype=float)
    for i, name in enumerate(HISTORY_FEATURES):
        out[name] = restored[:, i]
    return out[list(FEATURE_NAMES)]


@dataclass(frozen=True, slots=True)
class CardProfile:
    card_id: str
    gender: str
    dob: datetime
    city: str
    state: str
    city_pop: int


@dataclass(frozen=True, slots=True)
class CardContext:
    """Resumen legible del historial de la tarjeta, para mostrar en la web."""

    previous_purchases: int
    seconds_since_previous: float | None
    average_amount: float | None
    purchases_1h: int
    amount_1h: float
    purchases_24h: int
    amount_24h: float
    customer_age: int
    customer_gender: str
    city: str
    state: str


class CardHistory:
    """Historial de compras por tarjeta, en memoria, para calcular variables en vivo.

    Las transacciones analizadas por la API se agregan al historial (``record``),
    así varias compras seguidas de la misma tarjeta elevan su velocidad de uso.
    """

    def __init__(self, transactions: pd.DataFrame, profiles: list[CardProfile]) -> None:
        frame = transactions.sort_values(["card_id", "ts"], kind="stable")
        self._lock = threading.Lock()
        self._cards: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
        for card, group in frame.groupby("card_id", sort=False):
            self._cards[str(card)] = (
                group["ts"].to_numpy(dtype=np.int64),
                group["amt"].to_numpy(dtype=float),
                group["category"].to_numpy(dtype=object),
            )
        self._profiles = {profile.card_id: profile for profile in profiles}

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._profiles

    @property
    def card_count(self) -> int:
        return len(self._profiles)

    def profile(self, card_id: str) -> CardProfile:
        return self._profiles[card_id]

    def features_for(
        self,
        *,
        card_id: str,
        when: datetime,
        amount: float,
        category: str,
        distance_km: float,
        category_medians: dict[str, float],
    ) -> tuple[pd.DataFrame, CardContext]:
        profile = self._profiles[card_id]
        ts = pd.Series([pd.Timestamp(when).tz_localize(None)])
        row = _transaction_features(
            np.array([amount], dtype=float),
            ts,
            pd.Series([pd.Timestamp(profile.dob)]),
            np.array([1 if profile.gender == "M" else 0]),
            np.array([float(profile.city_pop)]),
            np.array([distance_km], dtype=float),
            pd.Series([category]),
            category_medians,
        )

        now = int(ts.iloc[0].value // 1_000_000_000)
        with self._lock:
            times, amounts, categories = self._cards.get(
                card_id, (np.empty(0, np.int64), np.empty(0), np.empty(0, object))
            )
            k = int(np.searchsorted(times, now, side="left"))  # solo compras anteriores
            prev_t, prev_a, prev_c = times[:k], amounts[:k], categories[:k]

        n = len(prev_t)
        mean = float(prev_a.mean()) if n else None
        std = float(np.sqrt(max(float((prev_a**2).mean()) - mean**2, 0.0))) if mean is not None else None
        history = {
            "compras_previas": float(n),
            "seg_desde_anterior": float(now - prev_t[-1]) if n else NO_PREVIOUS_SECONDS,
            "monto_vs_promedio_tarjeta": amount / (mean + 1) if mean is not None else 1.0,
            "monto_z_tarjeta": (amount - mean) / (std + 1) if mean is not None and std is not None else 0.0,
            "misma_categoria_previas": float(np.sum(prev_c == category)),
        }
        windows: dict[str, tuple[int, float]] = {}
        for name, seconds in WINDOWS:
            mask = prev_t > now - seconds
            count = int(mask.sum()) + 1  # la ventana incluye la compra actual
            total = float(prev_a[mask].sum()) + amount
            history[f"compras_{name}"] = float(count)
            history[f"monto_{name}"] = total
            windows[name] = (count, total)
        history["monto_vs_24h"] = amount / (history["monto_24h"] + 1)
        for name in HISTORY_FEATURES:
            row[name] = history[name]

        age = int((ts.iloc[0] - pd.Timestamp(profile.dob)).days // 365.25)
        context = CardContext(
            previous_purchases=n,
            seconds_since_previous=float(now - prev_t[-1]) if n else None,
            average_amount=round(mean, 2) if mean is not None else None,
            purchases_1h=windows["1h"][0],
            amount_1h=round(windows["1h"][1], 2),
            purchases_24h=windows["24h"][0],
            amount_24h=round(windows["24h"][1], 2),
            customer_age=age,
            customer_gender=profile.gender,
            city=profile.city,
            state=profile.state,
        )
        return row[list(FEATURE_NAMES)], context

    def record(self, *, card_id: str, when: datetime, amount: float, category: str) -> None:
        """Agrega una transacción analizada al historial de la tarjeta."""
        now = int(pd.Timestamp(when).tz_localize(None).value // 1_000_000_000)
        with self._lock:
            times, amounts, categories = self._cards.get(
                card_id, (np.empty(0, np.int64), np.empty(0), np.empty(0, object))
            )
            k = int(np.searchsorted(times, now, side="right"))
            self._cards[card_id] = (
                np.insert(times, k, now),
                np.insert(amounts, k, amount),
                np.insert(categories, k, category),
            )
