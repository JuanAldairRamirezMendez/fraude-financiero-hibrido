import { useQuery } from "@tanstack/react-query";

import { fetchModels } from "./api";

export const modelsQueryKey = ["models"] as const;

export function useModelsQuery() {
  return useQuery({
    queryKey: modelsQueryKey,
    queryFn: ({ signal }) => fetchModels(signal),
  });
}
