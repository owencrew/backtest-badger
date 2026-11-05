import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync, readdirSync } from "node:fs";
import { test } from "node:test";
import {
  study002,
  decimalParts,
  studyNumber,
  studyPercent,
  validateStudyAccounts,
  costBarWidth,
} from "../lib/study002";
import { markets } from "../lib/research";

const root = "../docs/studies/";
const assets = `${root}study-002-assets/`;
const read = (file: string) => readFileSync(file, "utf8");
const hash = (file: string) =>
  createHash("sha256").update(readFileSync(file)).digest("hex");
const review = JSON.parse(read(`${assets}review-data.json`));
const manifest = JSON.parse(read(`${assets}manifest.json`));
const report = read(`${root}study-002-slower-trend-results.md`);
const rows = report
  .split("\n")
  .filter((line) => line.startsWith("| "))
  .map((line) =>
    line
      .split("|")
      .slice(1, -1)
      .map((s) => s.trim()),
  );
const plain = (value: string, digits = 6, multiplier = 1n) =>
  studyNumber(value, digits, multiplier).replaceAll(",", "").replace("−", "-");
const names = {
  trend_30d_daily_v1: "30-Day Trend",
  ridge: "Ridge reference",
  cash: "Cash",
  buy_and_hold: "Buy & Hold",
};

test("immutable Study 002 sources, complete asset manifest and evidence hashes match", () => {
  assert.equal(
    study002.sourceRevision,
    "04c485e6af74e52d0541ceab3a88ca0debb21346",
  );
  for (const [file, expected] of Object.entries(study002.sourceHashes))
    assert.equal(hash(root + file), expected, file);
  for (const [file, pin] of Object.entries(manifest.files) as [
    string,
    { bytes: number; sha256: string },
  ][]) {
    assert.equal(readFileSync(assets + file).length, pin.bytes, file);
    assert.equal(hash(assets + file), pin.sha256, file);
  }
  for (const [field, expected] of Object.entries(study002.summaryHashes)) {
    assert.equal(review.source[field], expected);
    assert.equal(manifest.source[field], expected);
    const source = field.startsWith("study001")
      ? read("../docs/stage-04b2e5g-first-genuine-historical-backtest.md")
      : report;
    assert.ok(source.includes(expected), field);
  }
  const freeze = JSON.parse(read(root + "study-002-freeze.json"));
  for (const file of ["study-002-methodology.md", "study-002-config.json"])
    assert.equal(
      hash(root + file),
      freeze.files[`docs/studies/${file}`].sha256,
    );
  assert.deepEqual(readdirSync("public/research/study-002").sort(), [
    "drawdown.png",
    "equity.png",
    "exposure.png",
  ]);
  for (const file of readdirSync("public/research/study-002"))
    assert.equal(
      hash(`public/research/study-002/${file}`),
      manifest.files[file].sha256,
    );
});

test("period, units and all eight independently identified portfolios are explicit", () => {
  const config = JSON.parse(read(root + "study-002-config.json"));
  assert.equal(study002.periodStart, config.start);
  assert.equal(study002.lastMark, config.last_mark);
  assert.deepEqual(study002.units, {
    money: "USDT",
    returns: "dimensionless fraction",
    exposure: "seconds",
  });
  assert.equal(new Set(study002.accounts.map((a) => a.id)).size, 8);
  for (const symbol of ["BTCUSDT", "ETHUSDT"])
    assert.deepEqual(
      study002.accounts
        .filter((a) => a.symbol === symbol)
        .map((a) => a.strategy)
        .sort(),
      Object.keys(names).sort(),
    );
});

for (const a of study002.accounts) {
  test(`${a.symbol} ${a.strategy}: every public value equals exact review data and report summaries`, () => {
    const source = review.accounts.find(
      (s: { account_id: string }) => s.account_id === a.id,
    );
    assert.ok(source);
    assert.equal(source.status, "available");
    const expected = {
      id: source.account_id,
      symbol: source.symbol,
      strategy: source.label,
      initialFunding: source.initial_funding,
      firstEquity: source.first_mark_equity,
      finalEquity: source.final_mark_equity,
      returnFraction: source.performance.funding_relative_marked_return,
      drawdownFraction:
        source.performance.maximum_observed_hourly_reference_mark_drawdown,
      buys: source.costs_by_side.BUY.count,
      sells: source.costs_by_side.SELL.count,
      exposureSeconds: source.performance.exposure_seconds,
      fees: source.totals.fees,
      halfSpread: source.totals.hypothetical_half_spread,
      slippage: source.totals.hypothetical_slippage,
      totalCosts: source.totals.total_attributed_costs,
      sharpe: source.descriptive_statistics.zero_rate_sharpe,
      monthly: review.monthly
        .filter(
          (m: { symbol: string; strategy: string }) =>
            m.symbol === a.symbol && m.strategy === a.strategy,
        )
        .map((m: { start: string; complete: boolean; return: string }) => ({
          month: m.start.slice(0, 7),
          complete: m.complete,
          returnFraction: m.return,
        })),
    };
    assert.deepEqual(a, expected);
    const matches = rows.filter(
      (r) => r[0] === a.symbol && r[1] === names[a.strategy],
    );
    const main = matches.find((r) => r.length === 5)!;
    assert.equal(plain(a.firstEquity, 18).replace(/\.?0+$/, ""), main[2]);
    assert.equal(plain(a.finalEquity, 18).replace(/\.?0+$/, ""), main[3]);
    assert.equal(`${plain(a.returnFraction, 6, 100n)}%`, main[4]);
    const activity = matches.find(
      (r) => r.length === 7 && r[2].includes(" / "),
    )!;
    assert.equal(activity[2], `${a.buys} / ${a.sells}`);
    const costs = matches.find((r) => r.length === 8)!;
    assert.deepEqual(
      [a.fees, a.halfSpread, a.slippage, a.totalCosts].map((v) => plain(v)),
      costs.slice(4),
    );
    const risk = matches.find((r) => r.length === 6 && r[2].endsWith("%"))!;
    assert.equal(`${plain(a.drawdownFraction, 6, 100n)}%`, risk[3]);
    assert.equal(
      a.sharpe.value === null
        ? "Undefined (zero variance)"
        : plain(a.sharpe.value),
      risk[5],
    );
    const duration = matches.find(
      (r) => r.length === 5 && r[2] === String(a.exposureSeconds),
    );
    assert.ok(duration, "exact exposure seconds present in report");
    for (const [i, month] of a.monthly.entries()) {
      assert.equal(month.month, `2024-${String(i + 1).padStart(2, "0")}`);
      assert.equal(month.complete, i < 11);
      if (a.strategy === "cash") {
        assert.equal(decimalParts(month.returnFraction)[0], 0n);
        continue;
      }
      const row = rows.find(
        (r) =>
          r.length === 7 &&
          r[0] === `${month.month}${i === 11 ? " (partial)" : ""}`,
      )!;
      const index =
        (a.symbol === "BTCUSDT" ? 1 : 4) +
        ["trend_30d_daily_v1", "ridge", "buy_and_hold"].indexOf(a.strategy);
      assert.equal(`${plain(month.returnFraction, 6, 100n)}%`, row[index]);
    }
    if (a.strategy !== "trend_30d_daily_v1") {
      const old = markets
        .find((m) => m.symbol === a.symbol)!
        .accounts.find(
          (s) =>
            s.strategy ===
            (a.strategy === "ridge"
              ? "Ridge"
              : a.strategy === "cash"
                ? "Cash"
                : "Buy & Hold"),
        )!;
      assert.equal(
        studyPercent(a.returnFraction),
        `${Number(old.returnPct) > 0 ? "+" : Number(old.returnPct) < 0 ? "−" : ""}${Math.abs(Number(old.returnPct)).toFixed(2)}%`,
      );
      const [n, d] = decimalParts(a.finalEquity);
      const [oldN, oldD] = decimalParts(old.finalValue);
      assert.equal(n * oldD, oldN * d);
      assert.equal(a.buys, old.buys);
      assert.equal(a.sells, old.sells);
    }
  });
}

test("strict public allowlist rejects missing, nonfinite, extra and inconsistent data", () => {
  const mutations = [
    (a: Record<string, unknown>[]) => {
      a[0].private_evidence = "forbidden";
    },
    (a: Record<string, unknown>[]) => {
      delete a[0].fees;
    },
    (a: Record<string, unknown>[]) => {
      a[0].returnFraction = "NaN";
    },
    (a: Record<string, unknown>[]) => {
      a[0].finalEquity = Infinity;
    },
    (a: Record<string, unknown>[]) => {
      a[0].fees = null;
    },
    (a: Record<string, unknown>[]) => {
      a[0].fees = "1";
    },
    (a: Record<string, unknown>[]) => {
      a[0].finalEquity = "10000";
    },
    (a: Record<string, unknown>[]) => {
      a[1] = a[0];
    },
    (a: Record<string, unknown>[]) => {
      a[0].symbol = "ETHUSDT";
    },
    (a: Record<string, unknown>[]) => {
      a[0].buys = -1;
    },
    (a: Record<string, unknown>[]) => {
      a[0].monthly = [];
    },
    (a: Record<string, unknown>[]) => {
      a[3].sharpe = { value: "0", reason: null };
    },
  ];
  for (const mutate of mutations) {
    const copy = JSON.parse(JSON.stringify(study002.accounts));
    mutate(copy);
    assert.throws(() => validateStudyAccounts(copy));
  }
  for (const value of ["NaN", "Infinity", "", "1e300", "-1", "10001"])
    assert.throws(() => costBarWidth(value));
  const december = structuredClone(study002.accounts);
  december[0].monthly[11].complete = true;
  assert.throws(() => validateStudyAccounts(december));
  assert.equal(studyNumber("1.005"), "1.01");
  assert.equal(studyPercent("0.366249917617293100"), "+36.62%");
  assert.equal(studyPercent("-0.5795605761760247"), "−57.96%");
  assert.equal(
    study002.accounts.find((a) => a.strategy === "cash")!.sharpe.value,
    null,
  );
});

test("Study 001 presentation and seven editorial approvals retain their baseline bytes", () => {
  for (const [file, expected] of Object.entries({
    "lib/research.ts":
      "384cb644b96bfab2ff43fc8c2993ee07ff76bc694d8bd71e0638dab3a30b9020",
    "components/dig-explorer.tsx":
      "ed75bd53c061432deb65e2fbbc019d2e31d5b49ca8cd0de4caaa3d43f4339ae7",
    "components/performance-chart.tsx":
      "826276dcee11248b7a1ad00a4ab20ae0147eb01d533dd53ed065d36587808ccf",
    "components/ridge-explainer.tsx":
      "4e00c4cfff48eb3dc4fe24afc67f4aa8cd7df32f8a6e1541d8c7fd0c13952798",
    "content/publication-approvals.json":
      "4e36962e646f25c08f708e3bf77ec1beab798ffca92d73f1f69b35b9043c16e4",
  }))
    assert.equal(hash(file), expected, file);
});
