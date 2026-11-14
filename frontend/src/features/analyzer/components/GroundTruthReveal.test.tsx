import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { REAL_SAMPLES } from "../realSamples";
import { GroundTruthReveal } from "./GroundTruthReveal";

const fraud = REAL_SAMPLES.find((sample) => sample.isFraud)!;
const legit = REAL_SAMPLES.find((sample) => !sample.isFraud)!;

describe("GroundTruthReveal", () => {
  it("indica acierto cuando bloquea un fraude real", () => {
    render(<GroundTruthReveal sample={fraud} decision="block" />);
    expect(screen.getByText(/Era FRAUDE · el modelo acertó/)).toBeInTheDocument();
  });

  it("cuenta como acierto un fraude retenido para revisión", () => {
    render(<GroundTruthReveal sample={fraud} decision="review" />);
    expect(screen.getByText(/Era FRAUDE · el modelo acertó/)).toBeInTheDocument();
    expect(screen.getByText(/quedó retenido/)).toBeInTheDocument();
  });

  it("indica error cuando aprueba un fraude real", () => {
    render(<GroundTruthReveal sample={fraud} decision="approve" />);
    expect(screen.getByText(/el modelo se equivocó/)).toBeInTheDocument();
    expect(screen.getByText(/Fraude no detectado/)).toBeInTheDocument();
  });

  it("trata como falsa alarma leve una legítima retenida", () => {
    render(<GroundTruthReveal sample={legit} decision="review" />);
    expect(screen.getByText(/falsa alarma leve/)).toBeInTheDocument();
  });

  it("indica falsa alarma cuando bloquea una legítima", () => {
    render(<GroundTruthReveal sample={legit} decision="block" />);
    expect(screen.getByText(/Falsa alarma/)).toBeInTheDocument();
  });

  it("la muestra real está equilibrada entre fraudes y legítimas", () => {
    const frauds = REAL_SAMPLES.filter((sample) => sample.isFraud).length;
    expect(frauds).toBe(REAL_SAMPLES.length - frauds);
  });
});
