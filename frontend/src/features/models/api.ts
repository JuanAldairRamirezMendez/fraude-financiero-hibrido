import { env } from "@/config/env";
import { apiRequest } from "@/lib/api/client";
import { mockDelay } from "@/lib/api/mock";

import { mockModels } from "./mocks";
import type { ModelsData } from "./types";

const MOCK_LATENCY_MS = 400;

export async function fetchModels(signal?: AbortSignal): Promise<ModelsData> {
  if (!env.useMocks) {
    return apiRequest<ModelsData>("/models", { signal });
  }

  await mockDelay(MOCK_LATENCY_MS, signal);
  return mockModels;
}
