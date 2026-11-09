import type { IconName } from "@/components/ui/Icon";
import type { components } from "@/lib/api/schema";
import type { Tone } from "@/types/common";

export interface Kpi {
  id: string;
  label: string;
  value: string;
  trend: string;
  tone: Tone;
  icon: IconName;
  points: string;
}

export type TransactionStatus = "Flagged" | "Review" | "Approved";

export interface Transaction {
  id: string;
  occurredAt?: string;
  customer: string;
  amount: number;
  location: string;
  type: string;
  score: number;
  status: TransactionStatus;
}

export type OverviewQuery = components["schemas"]["OverviewResponse"];

export interface TransactionPageInfo {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

export interface OverviewData {
  kpis: Kpi[];
  transactions: Transaction[];
  transactionPage: TransactionPageInfo;
  totalTransactions: number;
  updatedAt: string;
  windowLabel: string;
}
