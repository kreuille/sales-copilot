// Generic formatting for AgentRun.outputPayload — used both for handoff
// pre-fill (FR-4.2) and for display, so a new agent works without adding
// per-agent formatting code (replaces the Phase 2 hand-written switch that
// only handled two agents).

export function flattenOutputForHandoff(output: unknown): string {
  if (!output || typeof output !== "object") return "";
  return Object.entries(output as Record<string, unknown>)
    .map(([key, value]) => `${key} : ${Array.isArray(value) ? value.join(" ; ") : String(value)}`)
    .join("\n");
}

// escalation-rules.md R-2: low-confidence markers the source prompts
// themselves ask the model to use ("inconnu", "signal faible"...) must be
// surfaced visibly, not buried in a paragraph.
const LOW_CONFIDENCE_MARKERS = [
  "inconnu",
  "signal faible",
  "signaux faibles",
  "information manquante",
  "non déterminé",
];

export function isLowConfidenceValue(value: unknown): boolean {
  if (typeof value !== "string") return false;
  const normalized = value.toLowerCase();
  return LOW_CONFIDENCE_MARKERS.some((marker) => normalized.includes(marker));
}
