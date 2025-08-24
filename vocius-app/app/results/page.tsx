/* -------------------------------------------------------------------------- */
/*  app/results/page.tsx – clean split + formatting                           */
/* -------------------------------------------------------------------------- */
"use client"

import { useEffect, useMemo, useState } from "react"
import { useRouter } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card, CardContent, CardHeader,
  CardTitle, CardDescription,
} from "@/components/ui/card"
import { Sparkles } from "lucide-react"
import { clearLastResult } from "@/lib/clearLastResult"

type AnyJson = Record<string, any>

/* ----------------------------- utils: parsing ----------------------------- */

const VERBAL_ANCHOR = /verbal\s*rfd\s*:?/i
const WRITTEN_ANCHOR =
  /(written\s*rfd(?:\s*and\s*speech[-\s]*by[-\s]*speech\s*flow\s*analysis)?\s*):?/i

/** Escape HTML, then we’ll add our own tags */
function esc(s: string) {
  return s.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;")
}

/** Normalize: strip **, trim, collapse >2 blank lines to one, normalize newlines */
function normalize(raw: string) {
  let s = raw.replace(/\r/g, "")
  s = s.replace(/\*\*/g, "")               // kill Markdown bold markers
  s = s.replace(/[ \t]+\n/g, "\n")         // trailing spaces
  s = s.replace(/\n{3,}/g, "\n\n")         // excessive blank lines
  return s.trim()
}

/** Try to find verbal/written inside one combined blob */
function splitCombinedBlob(blob: string) {
  const s = normalize(blob)
  const wMatch = s.search(WRITTEN_ANCHOR)
  const vMatch = s.search(VERBAL_ANCHOR)

  // If we see "Written RFD..." anywhere, treat everything before it as Verbal
  if (wMatch >= 0) {
    const before = s.slice(0, wMatch)
    const after  = s.slice(wMatch).replace(WRITTEN_ANCHOR, "").trim()
    // Remove a leading "Verbal RFD:" label if it’s there
    const verbal = before.replace(VERBAL_ANCHOR, "").trim()
    const written = after
    return { verbal, written }
  }

  // If we only find "Verbal RFD:", give verbal and leave written empty
  if (vMatch >= 0) {
    const verbal = s.replace(VERBAL_ANCHOR, "").trim()
    return { verbal, written: "" }
  }

  // Fallback: put the whole thing into written
  return { verbal: "", written: s }
}

/** Pull verbal/written from flexible shapes returned by backend */
function pickRfds(json: AnyJson) {
  const j  = json || {}
  const ja = j.judgeAnalysis ?? j.judge_feedback ?? j.feedback ?? {}

  let verbal =
    ja.verbalRfd ?? ja.verbal_rfd ?? j.verbalRfd ?? j.verbal_rfd ?? ""
  let written =
    ja.writtenRfd ?? ja.written_rfd ?? j.writtenRfd ?? j.written_rfd ?? ""

  // Some runs shove everything into a single "rfd" or "writtenRfd" with both sections.
  const combined =
    (typeof ja.rfd === "string" && ja.rfd) ||
    (typeof written === "string" && WRITTEN_ANCHOR.test(written) ? written : "") ||
    (typeof j.rfd === "string" && j.rfd) ||
    ""

  if ((!verbal || !verbal.trim()) && combined) {
    const split = splitCombinedBlob(combined)
    if (!verbal)  verbal  = split.verbal
    if (!written) written = split.written
  }

  // Last resort: the Flow Notes field sometimes carries the written block
  if ((!written || !written.trim()) && typeof j.flowNotes === "string") {
    written = j.flowNotes
  }

  return {
    verbal: normalize(String(verbal || "")),
    written: normalize(String(written || "")),
  }
}

/* --------------------------- utils: formatting ---------------------------- */

/**
 * Convert plain text into clean HTML:
 * - section headings like "Aff Constructive:" become <h3>
 * - paragraphs are compact (one blank line between sections)
 * - no Markdown ** artifacts remain (already removed in normalize)
 */
function toSectionedHTML(src: string) {
  if (!src) return "<p>Not provided.</p>"

  const HEADING = /^(?:Aff|Neg)\s+(?:Constructive|Rebuttal|Summary|Final\s*Focus)\s*:|^Crossfire\s*\d*\s*:|^Grand\s*Crossfire\s*:$/i

  const lines = esc(src).split("\n")
  const out: string[] = []
  let para: string[] = []

  const flushPara = () => {
    if (!para.length) return
    const text = para.join(" ").replace(/\s{2,}/g, " ").trim()
    if (text) out.push(`<p>${text}</p>`)
    para = []
  }

  for (let raw of lines) {
    const line = raw.trim()
    if (!line) { flushPara(); continue }

    if (HEADING.test(line)) {
      flushPara()
      out.push(`<h3 class="text-lg font-semibold mb-2">${line.replace(/:$/, "")}</h3>`)
    } else if (/^verbal\s*rfd\s*:$/i.test(line)) {
      // drop standalone "Verbal RFD:" labels inside written blocks
      flushPara()
    } else if (WRITTEN_ANCHOR.test(line)) {
      // drop standalone "Written RFD..." labels
      flushPara()
    } else {
      para.push(line)
    }
  }
  flushPara()

  // tighten spacing between blocks (keep one blank line)
  return out.join("\n")
}

/** Verbal RFD is simpler: just paragraphs, no section headings needed */
function toVerbalHTML(src: string) {
  if (!src) return "<p>Not provided.</p>"
  const s = esc(src)
    .replace(/\n{3,}/g, "\n\n")
    .trim()
  const parts = s.split(/\n{2,}/).map(p => p.trim()).filter(Boolean)
  return parts.map(p => `<p>${p}</p>`).join("\n")
}

/* -------------------------------------------------------------------------- */

export default function ResultsPage() {
  const router = useRouter()
  const [json, setJson] = useState<AnyJson | null>(null)

  useEffect(() => {
    const j = localStorage.getItem("vocius_last_result")
    if (j) { try { setJson(JSON.parse(j)) } catch {} }
  }, [])

  const { verbal, written } = useMemo(() => pickRfds(json ?? {}), [json])
  const hasAnything = !!verbal || !!written

  const verbalHTML  = useMemo(() => toVerbalHTML(verbal), [verbal])
  const writtenHTML = useMemo(() => toSectionedHTML(written), [written])

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-4xl font-bold">Analysis Results</h1>
        <div className="flex gap-3">
          <Button
            variant="secondary"
            onClick={() => {
              clearLastResult()
              router.push("/playground")
            }}
          >
            Back to Playground
          </Button>
          <Button
            onClick={() => {
              const blob = new Blob(
                [(written || verbal || "Thanks for using Vocius!")],
                { type: "text/plain" },
              )
              const url = URL.createObjectURL(blob)
              const a = document.createElement("a")
              a.href = url
              a.download = `analysis_${new Date().toISOString().replace(/[:.]/g, "-")}.txt`
              document.body.appendChild(a); a.click(); a.remove()
              URL.revokeObjectURL(url)
            }}
          >
            Download .txt
          </Button>
        </div>
      </div>

      {!hasAnything && (
        <Card>
          <CardHeader>
            <CardTitle>No formatted feedback found</CardTitle>
            <CardDescription>
              If you just ran the analysis, refresh once. Otherwise, re-run from the Playground.
            </CardDescription>
          </CardHeader>
        </Card>
      )}

      {hasAnything && (
        <>
          {/* Two-up: Verbal vs Flow Notes (Written) */}
          <div className="grid md:grid-cols-2 gap-6">
            <Card>
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Verbal RFD</CardTitle>
                <Badge variant="secondary">Summary</Badge>
              </CardHeader>
              <CardContent>
                <div
                  className="prose prose-sm max-w-none whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{ __html: verbalHTML }}
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex items-center justify-between">
                <CardTitle>Flow Notes</CardTitle>
                <Badge variant="secondary">Written</Badge>
              </CardHeader>
              <CardContent>
                <div
                  className="prose prose-sm max-w-none whitespace-pre-wrap"
                  dangerouslySetInnerHTML={{ __html: writtenHTML }}
                />
              </CardContent>
            </Card>
          </div>

          {/* CTA */}
          <Card className="mt-8 border-2">
            <CardHeader className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-vocius-orange" />
              <div>
                <CardTitle>New: Speech Metrics</CardTitle>
                <CardDescription>
                  After debate, sharpen delivery with pace, pauses, clarity, and pitch-range insights.
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="flex justify-end">
              <Button
                className="bg-vocius-orange hover:bg-vocius-orange-hover text-white"
                onClick={() => router.push("/playground")}
              >
                Try Speech Analysis
              </Button>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
