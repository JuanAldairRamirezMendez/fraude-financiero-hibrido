import { useQuery } from "@tanstack/react-query";

import { fetchOverview, type OverviewParams } from "./api";

export const overviewQueryKey = ["overview"] as const;

export function useOverviewQuery(params: OverviewParams = {}) {
  return useQuery({
    queryKey: [...overviewQueryKey, params],
    queryFn: ({ signal }) => fetchOverview(params, signal),
  });
}
