// Core data types for Vocius API

export interface AnalysisRequest {
  audioFile: File
  apiKeys: {
    openai: string
    huggingface: string
    openrouter: string
  }
}

export interface AnalysisProgress {
  judgingProgress: number
  deliveryProgress: number
  status: "processing" | "complete" | "error"
  logs: AnalysisLog[]
}

export interface AnalysisLog {
  timestamp: string
  message: string
  type: "info" | "success" | "error"
}

export interface JudgeAnalysis {
  overallScore: number
  rfd: string
  flowNotes: FlowNote[]
  verdict: string
}

export interface FlowNote {
  speech: string
  time: string
  notes: string
}

export interface DeliveryMetrics {
  overallScore: number
  pace: {
    averageWpm: number
    optimalRange: string
    score: number
    analysis: string
  }
  pauses: {
    totalPauses: number
    averageLength: number
    score: number
    analysis: string
  }
  pitchRange: {
    range: string
    variation: string
    score: number
    analysis: string
  }
  clarity: {
    score: number
    analysis: string
  }
  volume: {
    score: number
    analysis: string
  }
}

export interface AnalysisResults {
  id: string
  judgeAnalysis: JudgeAnalysis
  deliveryMetrics: DeliveryMetrics
  createdAt: string
  audioFileName: string
}

export interface User {
  id: string
  email: string
  name: string
  plan: "free" | "pro" | "team"
  analysesRemaining?: number
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}
