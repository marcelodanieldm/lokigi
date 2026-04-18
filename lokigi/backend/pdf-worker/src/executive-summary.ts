import { config } from "./config.js";
import { buildFallbackSummary, buildUserPrompt, SYSTEM_PROMPT, type ExecutiveSummaryInput } from "./prompts.js";

export type ExecutiveSummary = {
  paragraph_1_client_voice: string;
  paragraph_2_key_achievement: string;
  paragraph_3_improvement_opportunity: string;
};

function isValidSummary(value: any): value is ExecutiveSummary {
  return Boolean(
    value &&
    typeof value.paragraph_1_client_voice === "string" &&
    typeof value.paragraph_2_key_achievement === "string" &&
    typeof value.paragraph_3_improvement_opportunity === "string",
  );
}

export async function generateExecutiveSummary(input: ExecutiveSummaryInput): Promise<ExecutiveSummary> {
  if (!config.llmEnabled || !config.llmApiKey) {
    return buildFallbackSummary(input);
  }

  const endpoint = `${config.llmApiBase.replace(/\/$/, "")}/chat/completions`;
  const payload = {
    model: config.llmModel,
    temperature: 0.4,
    response_format: { type: "json_object" },
    messages: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: buildUserPrompt(input) },
    ],
  };

  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${config.llmApiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error(`Executive summary LLM failed: ${response.status}`);
    }

    const json = await response.json();
    const text = String(json?.choices?.[0]?.message?.content || "").trim();
    const parsed = JSON.parse(text);
    if (isValidSummary(parsed)) {
      return parsed;
    }
  } catch {
    // Fallback keeps PDF generation resilient.
  }

  return buildFallbackSummary(input);
}
