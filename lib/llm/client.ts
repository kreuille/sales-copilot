import "server-only";
import Anthropic from "@anthropic-ai/sdk";

// Server-only: the API key must never reach client bundles or logs
// (security-architecture.md "Secrets").
export const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
