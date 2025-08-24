import { type NextRequest, NextResponse } from "next/server"
import type { AnalysisResults } from "@/lib/types"
import { createSuccessResponse, createErrorResponse, delay } from "@/lib/api-helpers"

export async function GET(request: NextRequest, { params }: { params: { id: string } }) {
  try {
    const { id } = params

    // Simulate API delay
    await delay(500)

    // Mock results - in real app, this would fetch from database
    const mockResults: AnalysisResults = {
      id,
      audioFileName: "debate_recording.m4a",
      createdAt: new Date().toISOString(),
      judgeAnalysis: {
        overallScore: 85,
        rfd: `This debate demonstrated strong analytical skills with well-structured arguments. The affirmative case was compelling with solid evidence and clear impact calculus. However, there were missed opportunities for stronger rebuttals in the final speeches.

Key Strengths:
- Excellent use of evidence and citations
- Clear logical flow from premise to conclusion  
- Strong impact analysis and weighing
- Good time management throughout

Areas for Improvement:
- Could have addressed opponent's framework more directly
- Some arguments lacked sufficient warrant explanation
- Final rebuttal could have been more organized
- Consider stronger cross-examination strategy`,
        flowNotes: [
          {
            speech: "1AC",
            time: "8:00",
            notes: "Strong opening case. Clear plan text. Good solvency evidence. Impact: economic collapse → war.",
          },
          {
            speech: "1NC",
            time: "8:00",
            notes:
              "Topicality shell. Disadvantage: spending leads to inflation. Counterplan: private sector alternative.",
          },
          {
            speech: "2AC",
            time: "8:00",
            notes: "T response adequate. DA non-unique - inflation already happening. CP doesn't solve case.",
          },
          {
            speech: "2NC",
            time: "8:00",
            notes: "Extends T violation. DA impact turn - deflation worse. CP solvency evidence strong.",
          },
          {
            speech: "1NR",
            time: "5:00",
            notes: "Goes for T and CP. Drops DA. T standards analysis weak.",
          },
          {
            speech: "1AR",
            time: "5:00",
            notes: "T defense holds. CP perm argument. Case extensions solid.",
          },
          {
            speech: "2NR",
            time: "5:00",
            notes: "All-in on CP. Solvency comparison. Perm response insufficient.",
          },
          {
            speech: "2AR",
            time: "5:00",
            notes: "Case outweighs. Perm shields link. CP doesn't solve root cause.",
          },
        ],
        verdict: "Affirmative wins on case outweighs and counterplan doesn't solve.",
      },
      deliveryMetrics: {
        overallScore: 78,
        pace: {
          averageWpm: 185,
          optimalRange: "160-200",
          score: 82,
          analysis: "Good pace overall. Slightly fast during rebuttals but maintained clarity.",
        },
        pauses: {
          totalPauses: 47,
          averageLength: 1.2,
          score: 75,
          analysis: "Effective use of strategic pauses. Could reduce filler pauses between arguments.",
        },
        pitchRange: {
          range: "120-280 Hz",
          variation: "High",
          score: 80,
          analysis: "Excellent vocal variety. Good emphasis on key arguments. Maintain energy in rebuttals.",
        },
        clarity: {
          score: 85,
          analysis: "Clear articulation throughout. Minor issues with technical terms pronunciation.",
        },
        volume: {
          score: 72,
          analysis: "Generally appropriate volume. Could project more during cross-examination.",
        },
      },
    }

    return NextResponse.json(createSuccessResponse(mockResults))
  } catch (error) {
    console.error("Results fetch error:", error)
    return NextResponse.json(createErrorResponse("Internal server error"), { status: 500 })
  }
}
