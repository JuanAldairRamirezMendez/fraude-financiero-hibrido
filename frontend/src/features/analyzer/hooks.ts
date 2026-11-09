import { useMutation } from "@tanstack/react-query";

import { analyzeTransaction } from "./api";

export function useAnalyzeTransaction() {
  return useMutation({
    mutationFn: (input: Parameters<typeof analyzeTransaction>[0]) => analyzeTransaction(input),
  });
}
