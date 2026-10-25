import { REFRESH_MS } from "./market";
// One timer and one request per mounted feed. Also used by deterministic lifecycle tests.
export function startPolling(
  run: (signal: AbortSignal) => Promise<void>,
  environment: Pick<
    Document,
    "hidden" | "addEventListener" | "removeEventListener"
  > = document,
  interval = REFRESH_MS,
  timeout = 15_000,
) {
  let disposed = false;
  let controller: AbortController | undefined;
  let timer: ReturnType<typeof setTimeout> | undefined;
  const refresh = () => {
    clearTimeout(timer);
    controller?.abort();
    if (disposed || environment.hidden) return;
    const request = new AbortController();
    controller = request;
    const deadline = setTimeout(
      () => request.abort(new Error("Request timed out. Try again.")),
      timeout,
    );
    void run(request.signal).finally(() => {
      clearTimeout(deadline);
      if (!disposed && controller === request && !environment.hidden)
        timer = setTimeout(refresh, interval);
    });
  };
  const visibility = () => refresh();
  environment.addEventListener("visibilitychange", visibility);
  refresh();
  return {
    refresh,
    stop: () => {
      disposed = true;
      clearTimeout(timer);
      controller?.abort();
      environment.removeEventListener("visibilitychange", visibility);
    },
  };
}
