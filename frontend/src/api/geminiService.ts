import { GoogleGenAI } from "@google/genai";
import { SystemMetric, FeatureImportance } from '../types';

const getClient = () => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) return null;
  return new GoogleGenAI({ apiKey });
};

export const generateAIExplanation = async (
  currentMetrics: SystemMetric,
  importance: FeatureImportance[],
  isStorm: boolean
): Promise<string> => {
  const ai = getClient();
  if (!ai) {
    return "API Key not configured. Please check your environment variables to enable AI insights.";
  }

  const prompt = `
    You are an AI Controller for a high-availability distributed system.
    Analyze the current system state and explain why the autoscaling decision was made based on the XGBoost feature importance.
    
    Current State:
    - Status: ${isStorm ? "CRITICAL (Traffic Storm)" : "NORMAL"}
    - RPS (Requests Per Second): ${currentMetrics.rpsActual.toFixed(0)}
    - Predicted RPS: ${currentMetrics.rpsPredicted.toFixed(0)}
    - Active Servers: ${currentMetrics.activeServers}
    - CPU Utilization: ${currentMetrics.cpuUtilization.toFixed(1)}%
    - Memory Usage: ${currentMetrics.memoryUsage.toFixed(1)}%
    - Error Rate: ${currentMetrics.errorRate.toFixed(2)}%
    
    Top Factors (Feature Importance):
    ${importance.map(f => `- ${f.feature}: ${(f.importance * 100).toFixed(1)}%`).join('\n')}
    
    Provide a concise, professional explanation (max 2 sentences) suitable for a dashboard tooltip. Focus on the "Why".
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
    });
    return response.text || "Analysis unavailable.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    return "Unable to generate AI explanation at this time.";
  }
};