import Ollama from "ollama";
import { logger } from "./logger";

export const DEFAULT_MODEL = "gemma4:e2b";

const OLLAMA_OPTIONS = {
  temperature: 0.2, // Factual but human-sounding
  top_k: 40, // Varied action verbs
  top_p: 0.85, // Professional vocabulary limits
  num_predict: 4096, // Increased from 2048 to ensure 2-page CVs don't cut off
  num_ctx: 8192, // CRITICAL: Ensures it can read your whole Master CV
  repeat_penalty: 1.15, // OLLAMA SPECIFIC: Prevents the model from repeating itself
};

export async function callOllama(
  system: string,
  userMessage: string,
  model = DEFAULT_MODEL
): Promise<string> {
  logger.info(`Calling Ollama model '${model}'`);
  logger.debug(`System:\n${system}`);
  logger.debug(`User message:\n${userMessage}`);

  const response = await Ollama.chat({
    model,
    messages: [
      { role: "system", content: system },
      { role: "user", content: userMessage },
    ],
    options: OLLAMA_OPTIONS,
  });

  const result = response.message.content;
  logger.debug(`Response:\n${result}`);
  return result;
}
