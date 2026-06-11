import Anthropic from "@anthropic-ai/sdk";
import { logger } from "./logger";

export const DEFAULT_CLAUDE_MODEL = "claude-opus-4-7";

// Opus 4.7 removed temperature/top_p/top_k entirely (400 if sent).
// All prior Claude models accept temperature.
function supportsTemperature(model: string): boolean {
  return model !== "claude-opus-4-7";
}

export async function callClaude(
  system: string,
  userMessage: string,
  model = DEFAULT_CLAUDE_MODEL,
): Promise<string> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) throw new Error("ANTHROPIC_API_KEY environment variable is not set");

  logger.info(`Calling Claude model '${model}'`);
  logger.debug(`System:\n${system}`);
  logger.debug(`User message:\n${userMessage}`);

  const client = new Anthropic({ apiKey });

  const response = await client.messages.create({
    model,
    max_tokens: 2048,
    system: [
      {
        type:          "text",
        text:          system,
        cache_control: { type: "ephemeral" },
      },
    ],
    messages: [{ role: "user", content: userMessage }],
    ...(supportsTemperature(model) ? { temperature: 0 } : {}),
  });

  const textBlock = response.content.find((b) => b.type === "text");
  const result    = textBlock && textBlock.type === "text" ? textBlock.text : "";
  logger.debug(`Response:\n${result}`);
  return result;
}
