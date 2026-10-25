import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { test } from "node:test";
import {
  markets,
  percent,
  number,
  reportFile,
  research,
} from "../lib/research";

const report = readFileSync(`../docs/${reportFile}`, "utf8");
const rows = report
  .split("\n")
  .filter((line) => line.startsWith("| "))
  .map((line) =>
    line
      .split("|")
      .slice(1, -1)
      .map((s) => s.trim()),
  );
for (const market of markets) {
  for (const account of market.accounts) {
    test(`${market.symbol} ${account.strategy} matches authoritative account, risk and activity rows`, () => {
      const name = `${market.symbol} ${account.strategy}`;
      const matches = rows.filter((row) => row[0] === name);
      const values = matches.find(
        (row) => row.length === 5 && row[1] === research.initialCapital,
      );
      assert.ok(values, "funding/value row exists");
      assert.equal(values[3], account.finalValue);
      assert.equal(values[4], `${account.returnPct}%`);
      const risk = matches.find(
        (row) => row.length === 5 && row[1].endsWith("%"),
      );
      assert.ok(risk, "drawdown row exists");
      assert.equal(risk[2], `${account.drawdownPct}%`);
      const activity = matches.find(
        (row) => row.length === 5 && row[1].includes(" / "),
      );
      assert.ok(activity, "activity row exists");
      assert.equal(activity[1], `${account.buys} / ${account.sells}`);
      assert.equal(activity[3], account.turnover);
      assert.equal(activity[4], account.costs);
    });
  }
}
test("reported headline rounding and signs preserve losses, gains and cash", () => {
  assert.deepEqual(
    markets.map((m) => m.accounts.map((a) => percent(a.returnPct))),
    [
      ["−60.69%", "0.00%", "+120.81%"],
      ["−57.96%", "0.00%", "+46.18%"],
    ],
  );
  assert.deepEqual(
    markets.map((m) => number(m.accounts[0].costs)),
    ["9,932.12", "9,239.49"],
  );
});
