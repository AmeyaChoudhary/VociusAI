import { type NextRequest, NextResponse } from "next/server"
import type { User } from "@/lib/types"
import { createSuccessResponse, createErrorResponse, delay } from "@/lib/api-helpers"

export async function GET(request: NextRequest) {
  try {
    // Simulate API delay
    await delay(300)

    // Mock user profile - in real app, this would fetch from database using auth token
    const mockUser: User = {
      id: "user_demo123",
      email: "demo@vocius.ai",
      name: "Demo User",
      plan: "pro",
      analysesRemaining: 47,
    }

    return NextResponse.json(createSuccessResponse(mockUser))
  } catch (error) {
    console.error("Profile fetch error:", error)
    return NextResponse.json(createErrorResponse("Internal server error"), { status: 500 })
  }
}

export async function PUT(request: NextRequest) {
  try {
    const updates = await request.json()

    // Simulate API delay
    await delay(500)

    // Mock profile update - in real app, this would update database
    const updatedUser: User = {
      id: "user_demo123",
      email: updates.email || "demo@vocius.ai",
      name: updates.name || "Demo User",
      plan: "pro",
      analysesRemaining: 47,
    }

    return NextResponse.json(createSuccessResponse(updatedUser, "Profile updated successfully"))
  } catch (error) {
    console.error("Profile update error:", error)
    return NextResponse.json(createErrorResponse("Internal server error"), { status: 500 })
  }
}
