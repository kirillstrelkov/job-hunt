import { GoogleGenAI } from "@google/genai";
import { logger } from "./logger";

export const DEFAULT_GEMINI_MODEL = "gemini-2.0-flash";

export async function callGemini(
  system: string,
  userMessage: string,
  model = DEFAULT_GEMINI_MODEL
): Promise<string> {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey)
    throw new Error("GEMINI_API_KEY environment variable is not set");

  logger.info(`Calling Gemini model '${model}'`);
  logger.debug(`System:\n${system}`);
  logger.debug(`User message:\n${userMessage}`);

  const ai = new GoogleGenAI({ apiKey });
  const response = await ai.models.generateContent({
    model,
    contents: userMessage,
    config: {
      systemInstruction: system,
      temperature: 0.2,
      topK: 40, // Allows for varied vocabulary (good for action verbs)
      topP: 0.85, // Prevents robotic repetition
      maxOutputTokens: 8192, // Safely accommodates a full 2-page Markdown CV
    },
  });

  const result = response.text ?? "";
  logger.debug(`Response:\n${result}`);
  return result;
}
