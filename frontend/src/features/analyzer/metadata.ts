import { useQuery } from "@tanstack/react-query";

import { env } from "@/config/env";
import { apiRequest } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";

export type MetadataResponse = components["schemas"]["MetadataResponse"];

export function useMetadataQuery() {
  return useQuery({
    queryKey: ["metadata"],
    queryFn: ({ signal }) => apiRequest<MetadataResponse>("/metadata", { signal }),
    enabled: !env.useMocks,
    staleTime: 60_000,
  });
}
