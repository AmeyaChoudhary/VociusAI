import { type NextRequest, NextResponse } from "next/server"
import type { User } from "@/lib/types"
import { createSuccessResponse, createErrorResponse, generateMockUserId, delay } from "@/lib/api-helpers"

export async function POST(request: NextRequest) {
  try {
    const { email, password } = await request.json()

    // Validate input
    if (!email || !password) {
      return NextResponse.json(createErrorResponse("Email and password are required"), { status: 400 })
    }

    // Simulate authentication delay
    await delay(800)

    // Mock authentication - in real app, this would verify credentials
    if (email === "demo@vocius.ai" && password === "demo123") {
      const mockUser: User = {
        id: generateMockUserId(),
        email,
        name: "Demo User",
        plan: "pro",
        analysesRemaining: 50,
      }

      return NextResponse.json(createSuccessResponse(mockUser, "Login successful"))
    }

    // Mock successful login for any valid email format
    if (email.includes("@") && password.length >= 6) {
      const mockUser: User = {
        id: generateMockUserId(),
        email,
        name: email.split("@")[0],
        plan: "free",
        analysesRemaining: 3,
      }

      return NextResponse.json(createSuccessResponse(mockUser, "Login successful"))
    }

    return NextResponse.json(createErrorResponse("Invalid credentials"), { status: 401 })
  } catch (error) {
    console.error("Login error:", error)
    return NextResponse.json(createErrorResponse("Internal server error"), { status: 500 })
  }
}
