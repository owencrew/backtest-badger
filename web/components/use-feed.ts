"use client";
import { useEffect, useRef, useState } from "react";
import { startPolling } from "@/lib/polling";
export function useFeed<T>(loader: (signal: AbortSignal) => Promise<T>) {
  const [state, setState] = useState<{
    data?: T;
    loading: boolean;
    error?: string;
    checkedAt: number;
  }>({ loading: true, checkedAt: 0 });
  const refresh = useRef<() => void>(() => {});
  useEffect(() => {
    let active = true;
    let generation = 0;
    const polling = startPolling(async (signal) => {
      const current = ++generation;
      setState((old) => ({ ...old, loading: true, checkedAt: Date.now() }));
      try {
        const data = await loader(signal);
        if (active && !signal.aborted && current === generation)
          setState({ data, loading: false, checkedAt: Date.now() });
      } catch (error) {
        if (active && current === generation)
          setState((old) => ({
            ...old,
            loading: false,
            checkedAt: Date.now(),
            error:
              signal.aborted && signal.reason instanceof Error
                ? signal.reason.message
                : error instanceof Error
                  ? error.message
                  : "Data unavailable.",
          }));
      }
    });
    refresh.current = polling.refresh;
    return () => {
      active = false;
      polling.stop();
    };
  }, [loader]);
  return { ...state, refresh: () => refresh.current() };
}
