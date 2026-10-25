import assert from "node:assert/strict";
import { test } from "node:test";
import { startPolling } from "../lib/polling";
class Visibility extends EventTarget {
  hidden = false;
  change(hidden: boolean) {
    this.hidden = hidden;
    this.dispatchEvent(new Event("visibilitychange"));
  }
}
const flush = async () => {
  await Promise.resolve();
  await Promise.resolve();
};
test("one refresh timer; manual refresh, hide/resume and cleanup do not multiply polling", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const page = new Visibility();
  let calls = 0;
  const poll = startPolling(
    async () => {
      calls++;
    },
    page,
    300_000,
  );
  await flush();
  assert.equal(calls, 1);
  t.mock.timers.tick(300_000);
  await flush();
  assert.equal(calls, 2);
  poll.refresh();
  await flush();
  assert.equal(calls, 3);
  t.mock.timers.tick(300_000);
  await flush();
  assert.equal(calls, 4);
  page.change(true);
  t.mock.timers.tick(900_000);
  await flush();
  assert.equal(calls, 4);
  page.change(false);
  await flush();
  assert.equal(calls, 5);
  poll.stop();
  t.mock.timers.tick(900_000);
  page.change(false);
  await flush();
  assert.equal(calls, 5);
});
test("pending requests are aborted on replacement, hidden page, deadline and disposal", async (t) => {
  t.mock.timers.enable({ apis: ["setTimeout"] });
  const page = new Visibility();
  const signals: AbortSignal[] = [];
  const poll = startPolling(
    (signal) => {
      signals.push(signal);
      return new Promise<void>((resolve) =>
        signal.addEventListener("abort", () => resolve()),
      );
    },
    page,
    300_000,
    15_000,
  );
  poll.refresh();
  assert.equal(signals[0].aborted, true);
  page.change(true);
  assert.equal(signals[1].aborted, true);
  page.change(false);
  t.mock.timers.tick(15_000);
  assert.equal(signals[2].aborted, true);
  await flush();
  poll.refresh();
  poll.stop();
  assert.equal(signals[3].aborted, true);
});
