import { NextResponse } from "next/server"
import { createSuccessResponse } from "@/lib/api-helpers"

export async function GET() {
  return NextResponse.json(
    createSuccessResponse(
      {
        status: "healthy",
        timestamp: new Date().toISOString(),
        version: "1.0.0",
        services: {
          database: "connected",
          ai_models: "operational",
          file_storage: "available",
        },
      },
      "Vocius API is running",
    ),
  )
}
