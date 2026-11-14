import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { env } from "@/config/env";
import { apiRequest } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type FraudCase = components["schemas"]["CaseResponse"];
export type CaseStatus = FraudCase["status"];
export type CaseVerdict = NonNullable<FraudCase["verdict"]>;
type CaseListResponse = components["schemas"]["CaseListResponse"];
type CaseUpdate = components["schemas"]["CaseUpdateRequest"];

export const CASES_KEY = ["cases"] as const;
/** La cola se refresca sola para que los casos abiertos desde el Analizador aparezcan en vivo. */
export const CASES_REFRESH_MS = 5_000;

export const PENDING_STATUSES: ReadonlySet<CaseStatus> = new Set(["new", "in_review", "escalated"]);

export const isPending = (item: FraudCase) => PENDING_STATUSES.has(item.status);

export function useCasesQuery(refetchInterval: number | false = CASES_REFRESH_MS) {
  return useQuery({
    queryKey: CASES_KEY,
    queryFn: ({ signal }) => apiRequest<CaseListResponse>("/cases", { signal }),
    enabled: !env.useMocks,
    refetchInterval,
    retry: false,
  });
}

export function useUpdateCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, changes }: { id: string; changes: CaseUpdate }) =>
      apiRequest<FraudCase>(`/cases/${id}`, { method: "PATCH", body: changes }),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: CASES_KEY }),
  });
}

export const STATUS_LABELS: Record<CaseStatus, string> = {
  new: "Nuevo",
  in_review: "En revisión",
  escalated: "Escalado",
  resolved: "Resuelto",
};

export const VERDICT_LABELS: Record<CaseVerdict, string> = {
  confirmed_fraud: "Fraude confirmado",
  false_positive: "Liberada (legítima)",
  inconclusive: "Inconcluso",
};
