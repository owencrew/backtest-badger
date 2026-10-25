import assert from "node:assert/strict";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { test } from "node:test";

const output = path.join(process.cwd(), "out");
function files(directory: string): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? files(path.join(directory, entry.name))
      : [path.join(directory, entry.name)],
  );
}
test(
  "production export excludes draft article text and draft routes",
  {
    skip:
      !existsSync(output) &&
      "Run pnpm build first to inspect production output",
  },
  () => {
    const forbidden = [
      "A strategy can hold a position across several forecasts",
      "A price can be recorded correctly and still be the wrong price",
      "The archive downloaded successfully",
      "One of our first simulated trading strategies nearly doubled",
      "A backtest applies a specified decision rule",
      "A portfolio's final return tells you",
      "A forecast estimates an outcome.",
    ];
    const exported = files(output);
    for (const file of exported) {
      assert.doesNotMatch(file, /\/(field-notes|field-guide)\/\d{3}-/);
      if (/\.(html|txt|js|json)$/.test(file)) {
        const contents = readFileSync(file, "utf8");
        for (const text of forbidden)
          assert.equal(
            contents.includes(text),
            false,
            `Unapproved draft leaked to ${file}`,
          );
      }
    }
  },
);
