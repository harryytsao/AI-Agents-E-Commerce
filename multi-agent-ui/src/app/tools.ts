import { tool } from "ai";
import { z } from "zod";

export const commonTools = {
  getWeather: tool({
    description: "Get the weather for a location",
    parameters: z.object({
      location: z.string().describe("The location to get weather for"),
    }),
    execute: async ({ location }) => {
      // Simulate weather API call
      return {
        temperature: Math.round(Math.random() * 30),
        condition: "Sunny",
      };
    },
  }),
  searchWeb: tool({
    description: "Search the web for information",
    parameters: z.object({
      query: z.string().describe("The search query"),
    }),
    execute: async ({ query }) => {
      // Simulate web search
      return {
        results: [`Result for ${query}`, `Another result for ${query}`],
      };
    },
  }),
};
