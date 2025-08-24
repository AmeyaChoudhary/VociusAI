// app/api/analyze/route.ts
import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
    // figure out which analysis
    const { searchParams } = new URL(req.url)
    const type = searchParams.get("type") ?? "speech" // "speech" | "debate"

    // everything sent from the Playground
    const formData = await req.formData()

    // ---- call the FastAPI backend ----------------------------------------
    const backend = process.env.BACKEND_URL || "http://127.0.0.1:5057"
    const url = `${backend}/analyze/${type}`

      const upstream = await fetch(url, {
      method: "POST",
      body: formData as any,
      // @ts-expect-error  ── Node fetch needs this, but TS types don’t know yet
      duplex: "half",
  })


    // stream the FastAPI response back to the browser
    const text = await upstream.text()
    return new NextResponse(text, {
      status: upstream.status,
      headers: { "content-type": upstream.headers.get("content-type") ?? "text/plain" },
    })
  } catch (err: any) {
    console.error("[/api/analyze] proxy error:", err)
    return NextResponse.json({ error: String(err?.message || err) }, { status: 500 })
  }
}
