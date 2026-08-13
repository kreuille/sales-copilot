import { describe, expect, it } from "vitest";
import { flattenOutputForHandoff, isLowConfidenceValue } from "@/lib/prompt-engine/format-output";

describe("flattenOutputForHandoff", () => {
  it("formats a flat object as key : value lines", () => {
    const text = flattenOutputForHandoff({ who_summary: "Head of Sales", current_obsession: "Scaling" });
    expect(text).toBe("who_summary : Head of Sales\ncurrent_obsession : Scaling");
  });

  it("joins array values with a separator", () => {
    const text = flattenOutputForHandoff({ top_3_signals: ["funding", "hiring", "new CTO"] });
    expect(text).toBe("top_3_signals : funding ; hiring ; new CTO");
  });

  it("returns an empty string for non-object output", () => {
    expect(flattenOutputForHandoff(null)).toBe("");
    expect(flattenOutputForHandoff("plain text")).toBe("");
  });
});

describe("isLowConfidenceValue", () => {
  it("flags BR-1 markers like 'inconnu' or 'signal faible'", () => {
    expect(isLowConfidenceValue("inconnu")).toBe(true);
    expect(isLowConfidenceValue("Rôle inconnu, pas assez d'infos")).toBe(true);
    expect(isLowConfidenceValue("Signaux faibles détectés")).toBe(true);
  });

  it("does not flag ordinary confident output", () => {
    expect(isLowConfidenceValue("Head of Sales chez Acme depuis 2 ans")).toBe(false);
  });

  it("does not flag non-string values", () => {
    expect(isLowConfidenceValue(9)).toBe(false);
    expect(isLowConfidenceValue(["a", "b"])).toBe(false);
  });
});
