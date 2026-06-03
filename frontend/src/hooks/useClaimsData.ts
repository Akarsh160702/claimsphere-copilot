import { useQuery } from "@tanstack/react-query";
import { useEffect, useMemo } from "react";
import { fetchClaims, fetchHealth, computeMetrics } from "@/api/claims";
import { useAppStore } from "@/store/useAppStore";

/** Claims list + derived metrics, with live/synthetic source tracking. */
export function useClaimsData() {
  const setDataSource = useAppStore((s) => s.setDataSource);

  const query = useQuery({
    queryKey: ["claims"],
    queryFn: fetchClaims,
    refetchInterval: 30000,
    staleTime: 15000,
  });

  useEffect(() => {
    if (query.data) setDataSource(query.data.source);
  }, [query.data, setDataSource]);

  const claims = query.data?.claims ?? [];
  const metrics = useMemo(() => computeMetrics(claims), [claims]);

  return {
    claims,
    metrics,
    source: query.data?.source ?? "synthetic",
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
  };
}

/** Polls backend /health and reflects status into the global store. */
export function useBackendHealth() {
  const setBackendOnline = useAppStore((s) => s.setBackendOnline);

  const query = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 20000,
  });

  useEffect(() => {
    setBackendOnline(!!query.data && query.data.status === "healthy");
  }, [query.data, setBackendOnline]);

  return query.data;
}
