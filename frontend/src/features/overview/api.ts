import { env } from "@/config/env";
import { apiRequest } from "@/lib/api/client";
import { mockDelay } from "@/lib/api/mock";

import { mockOverview } from "./mocks";
import type { OverviewQuery, OverviewData, Transaction } from "./types";

const MOCK_LATENCY_MS = 350;

export interface OverviewParams {
  page?: number;
  pageSize?: number;
  q?: string;
  transactionType?: string;
}

function mapTransaction(item: OverviewQuery["transactions"]["items"][number]): Transaction {
  return {
    id: item.id,
    customer: item.customerId,
    amount: item.amount,
    location: `${item.region}, ${item.country}`,
    type: item.transactionType,
    score: item.score,
    status: item.status,
  };
}

function mapOverview(response: OverviewQuery): OverviewData {
  const toneById: Record<string, OverviewData["kpis"][number]["tone"]> = {
    transactions: "blue",
    "fraud-rate": "green",
    "f1-score": "purple",
    "pending-alerts": "orange",
  };
  const iconById: Record<string, OverviewData["kpis"][number]["icon"]> = {
    transactions: "card",
    "fraud-rate": "activity",
    "f1-score": "target",
    "pending-alerts": "clock",
  };
  return {
    kpis: response.kpis.map((kpi) => ({
      ...kpi,
      tone: toneById[kpi.id] ?? "blue",
      icon: iconById[kpi.id] ?? "activity",
      points: kpi.dataPoints.join(","),
    })),
    transactions: response.transactions.items.map(mapTransaction),
    transactionPage: response.transactions,
    totalTransactions: response.totalTransactions,
    updatedAt: response.updatedAt,
    windowLabel: response.windowLabel,
  };
}

export async function fetchOverview(
  params: OverviewParams = {},
  signal?: AbortSignal,
): Promise<OverviewData> {
  if (!env.useMocks) {
    const query = new URLSearchParams();
    query.set("page", String(params.page ?? 1));
    query.set("pageSize", String(params.pageSize ?? 5));
    if (params.q) query.set("q", params.q);
    if (params.transactionType) query.set("transactionType", params.transactionType);
    const response = await apiRequest<OverviewQuery>(`/overview?${query}`, { signal });
    return mapOverview(response);
  }

  await mockDelay(MOCK_LATENCY_MS, signal);
  return {
    ...mockOverview,
    transactionPage: {
      page: 1,
      pageSize: mockOverview.transactions.length,
      total: mockOverview.transactions.length,
      totalPages: 1,
    },
  };
}
