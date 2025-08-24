import type { ApiResponse } from "./types"

// Helper functions for API responses
export function createSuccessResponse<T>(data: T, message?: string): ApiResponse<T> {
  return {
    success: true,
    data,
    message,
  }
}

export function createErrorResponse(error: string): ApiResponse<never> {
  return {
    success: false,
    error,
  }
}

// Mock data generators
export function generateMockAnalysisId(): string {
  return `analysis_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

export function generateMockUserId(): string {
  return `user_${Math.random().toString(36).substr(2, 9)}`
}

// Simulate API delay
export function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Validate API keys format (mock validation)
export function validateApiKeys(keys: { openai: string; huggingface: string; openrouter: string }): boolean {
  return keys.openai.startsWith("sk-") && keys.huggingface.startsWith("hf_") && keys.openrouter.startsWith("sk-or-")
}
