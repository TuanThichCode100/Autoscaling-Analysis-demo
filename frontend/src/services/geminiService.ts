import { GoogleGenerativeAI } from "@google/generative-ai";
import { SystemMetric, FeatureImportance } from "../types";

// Initialize Gemini API
// ERROR: Property 'env' does not exist on type 'ImportMeta'.
// FIX: Ensure vite-env.d.ts is present and included in tsconfig.json
const API_KEY = import.meta.env.VITE_GEMINI_API_KEY || '';

// We'll use a mocked response if no API key is provided to prevent crashes
const MOCK_RESPONSE = "System is running optimally. No significant anomalies detected in RPS or CPU usage. Autoscaling is currently inactive.";

export const generateAIExplanation = async (
    metrics: SystemMetric,
    featureImportance: FeatureImportance[],
    isStormActive: boolean
): Promise<string> => {
    if (!API_KEY) {
        console.warn("Gemini API Key is missing. Using mock response.");
        // Simulate delay
        await new Promise(resolve => setTimeout(resolve, 1000));
        return isStormActive
            ? "CRITICAL ALERT: High traffic detected due to Storm Simulation. System is scaling up to handle the load."
            : MOCK_RESPONSE;
    }

    try {
        const genAI = new GoogleGenerativeAI(API_KEY);
        const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

        const prompt = `
      Analyze the following cloud system state and provide a concise operational insight (max 2 sentences).
      
      Current Metrics:
      - RPS: ${metrics.rpsActual}
      - CPU: ${metrics.cpuUtilization}%
      - Active Servers: ${metrics.activeServers}
      - Storm Mode: ${isStormActive}
      
      Top Influencing Factors:
      ${featureImportance.map(f => `- ${f.feature}: ${(f.importance * 100).toFixed(1)}%`).join('\n')}
      
      Explain why the system is in its current state (Scaling Up, Scaling Down, or Stable).
    `;

        const result = await model.generateContent(prompt);
        const response = await result.response;
        return response.text();
    } catch (error) {
        console.error("Gemini API Error:", error);
        return "Error generating insight. Please check API configuration.";
    }
};
