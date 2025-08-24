// app/api/tts/route.ts
import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
    const { text, voice = "Rachel" } = await req.json()
    if (!text || typeof text !== "string") {
      return new NextResponse("Missing text", { status: 400 })
    }
    const key = process.env.ELEVENLABS_API_KEY
    if (!key) return new NextResponse("ELEVENLABS_API_KEY not set", { status: 500 })

    const resp = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voice)}`, {
      method: "POST",
      headers: {
        "xi-api-key": key,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        voice_settings: { stability: 0.5, similarity_boost: 0.75 },
        model_id: "eleven_multilingual_v2",
      }),
    })

    if (!resp.ok) {
      const err = await resp.text()
      return new NextResponse(err || "TTS failed", { status: 502 })
    }

    const audio = await resp.arrayBuffer()
    return new NextResponse(new Uint8Array(audio), {
      status: 200,
      headers: {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "no-store",
      },
    })
  } catch (e: any) {
    return new NextResponse(e?.message || "TTS error", { status: 500 })
  }
}