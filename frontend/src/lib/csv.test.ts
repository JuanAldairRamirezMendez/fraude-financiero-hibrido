import { describe, expect, it } from "vitest";

import { toCsv } from "./csv";

describe("toCsv", () => {
  it("añade BOM y separa filas con CRLF", () => {
    const csv = toCsv([
      ["a", "b"],
      ["c", "d"],
    ]);

    expect(csv.startsWith("\uFEFF")).toBe(true);
    expect(csv).toBe('\uFEFF"a","b"\r\n"c","d"');
  });

  it("escapa comillas dobles", () => {
    const csv = toCsv([['He said "hi"']]);

    expect(csv).toContain('"He said ""hi"""');
  });

  it("neutraliza fórmulas de hoja de cálculo", () => {
    const csv = toCsv([["=SUM(A1:A2)", "+1", "-2", "@cmd", "\tvalor"]]);

    expect(csv).toContain('"\'=SUM(A1:A2)"');
    expect(csv).toContain('"\'+1"');
    expect(csv).toContain('"\'-2"');
    expect(csv).toContain('"\'@cmd"');
    expect(csv).toContain('"\'\tvalor"');
  });
});
