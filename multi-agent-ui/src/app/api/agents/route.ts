import { openai } from "@ai-sdk/openai";
import { streamText, convertToCoreMessages } from "ai";
import { commonTools } from "../../tools";

export const maxDuration = 30;

const agents = {
  assistant: openai("gpt-4o-mini"),
  researcher: openai("gpt-4o-mini"),
  analyst: openai("gpt-4o-mini"),
};

export async function POST(req: Request) {
  const { messages, agent } = await req.json();

  if (!agents[agent]) {
    return new Response("Invalid agent", { status: 400 });
  }

  const result = await streamText({
    model: agents[agent],
    messages: convertToCoreMessages(messages),
    tools: commonTools,
    system: `You are the ${agent} agent. Use the provided tools when necessary.`,
  });

  return result.toDataStreamResponse();
}
