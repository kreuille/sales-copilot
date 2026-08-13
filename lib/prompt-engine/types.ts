// Shapes of the JSON stored in AgentPromptVersion.inputSchema/outputSchema —
// mirrors the structure authored in agents/registry.yaml (see seed-agents.mjs).

export interface InputFieldSpec {
  field: string;
  source: string;
  // `kind` is present only on fields the PromptEngine actually reads
  // (workspace_context/user_input/deal_history). Entries whose source is
  // another agent's id are handoff/pre-fill hints for the UI (FR-4.2) and
  // have no `kind` — that absence is what tells resolveInputs/assemblePrompt
  // to skip them. `prefills` on a hint names the real field it pre-fills.
  kind?: "inline" | "content_block";
  placeholder?: string;
  required?: boolean;
  prefills?: string;
  note?: string;
}

export type OutputFieldType = "string" | "integer" | "string[3]" | "string[]" | "enum";

export interface OutputFieldSpec {
  field: string;
  type: OutputFieldType;
  description?: string;
  values?: string[];
}
