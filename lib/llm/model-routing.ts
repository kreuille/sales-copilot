// Model routing is a configuration concern, not an architectural one — the
// mapping can change as Claude's model lineup evolves without touching the
// agents that reference a class (agent-architecture.md "Classes de modèle").
export type ModelClass = "FAST" | "BALANCED" | "DEEP_REASONING";

const MODEL_BY_CLASS: Record<ModelClass, string> = {
  FAST: "claude-haiku-4-5-20251001",
  BALANCED: "claude-sonnet-5",
  DEEP_REASONING: "claude-opus-5",
};

// Several agents (analyste de pipeline, stratège de closing...) legitimately
// produce long multi-item structured output. A too-low cap here doesn't
// error — it silently truncates the tool call mid-object, which then fails
// Zod validation with a confusing "missing field" rather than a token-limit
// error. Sized generously per class rather than tuned per agent.
const MAX_TOKENS_BY_CLASS: Record<ModelClass, number> = {
  FAST: 2048,
  BALANCED: 4096,
  DEEP_REASONING: 8192,
};

export function resolveModel(modelClass: ModelClass): string {
  return MODEL_BY_CLASS[modelClass];
}

export function resolveMaxTokens(modelClass: ModelClass): number {
  return MAX_TOKENS_BY_CLASS[modelClass];
}
