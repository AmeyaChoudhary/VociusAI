/* -------------------------------------------------------------------------- */
/*  app/playground/page.tsx – Vocius Playground (polished flow + better ticker)
    - Restores the nicer layout you liked
    - Keeps improved staged console + progress (no stall at 65%)
    - Opens results in a NEW tab and never re-runs
    - Optional "ding" sound when complete
/* -------------------------------------------------------------------------- */
"use client"

import React, { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { toast } from "sonner"
import { Upload, Mic, Users, Key, Clock, Sparkles } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

/* ----------------------------------------------------------------------------
   Utils
---------------------------------------------------------------------------- */
async function postForm(url: string, form: FormData) {
  const res = await fetch(url, { method: "POST", body: form })
  if (!res.ok) {
    const msg = await res.text().catch(() => res.statusText)
    throw new Error(msg || "Request failed")
  }
  return res.json()
}

const niceTime = () => new Date().toLocaleTimeString()

/* Soft chime on completion */
function ding() {
  try {
    const Ctx: any = (window as any).AudioContext || (window as any).webkitAudioContext
    const ctx = new Ctx()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.type = "sine"
    o.frequency.value = 880
    o.connect(g); g.connect(ctx.destination)
    g.gain.setValueAtTime(0.0001, ctx.currentTime)
    g.gain.exponentialRampToValueAtTime(0.25, ctx.currentTime + 0.02)
    o.start()
    g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.22)
    o.stop(ctx.currentTime + 0.25)
  } catch { /* noop */ }
}

/* ============================================================================
   Component
=========================================================================== */
export default function PlaygroundPage() {
  const router = useRouter()

  /* ----------------------------   STATE   ---------------------------- */
  const [step, setStep] = useState<1 | 2>(1) // 1: API Keys, 2: Analyze
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)

  const [apiKeys, setApiKeys] = useState({ assemblyai: "", openrouter: "" })
  const aaiOk = useMemo(() => apiKeys.assemblyai.trim().length >= 16, [apiKeys])
  const orOk  = useMemo(() => apiKeys.openrouter.trim().length >= 16, [apiKeys])
  const canNext = aaiOk && orOk

  const [debateMeta, setDebateMeta] = useState({
    topic: "",
    first: "Aff",
    style: "tech",
  })

  type JobState = "idle" | "running" | "done" | "error"
  const [job, setJob] = useState<JobState>("idle")
  const [progress, setProgress] = useState<number>(0)
  const [logs, setLogs] = useState<string[]>([])
  const tickerRef = useRef<number | null>(null)
  const stageTimers = useRef<number[]>([])

  // keep a copy so "View Results" never re-runs
  const [lastResult, setLastResult] = useState<any | null>(null)

  /* ---------------------------   HELPERS   --------------------------- */
  const canAnalyze = useMemo(() => !!file && canNext, [file, canNext])

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(e.type === "dragenter" || e.type === "dragover")
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    const up = e.dataTransfer.files?.[0]
    if (up) setFile(up)
  }, [])

  const handleFilePick = (e: React.ChangeEvent<HTMLInputElement>) => {
    const up = e.target.files?.[0]
    if (up) setFile(up)
  }

  const appendLog = (line: string) =>
    setLogs((L) => [...L, `[${niceTime()}] ${line}`].slice(-300))

  function startTicker() {
    // clean old timers
    if (tickerRef.current) clearInterval(tickerRef.current)
    stageTimers.current.forEach(clearTimeout)
    stageTimers.current = []

    setProgress(3)
    appendLog("Uploading…")

    // staged console updates so it feels alive while waiting for the single HTTP call
    stageTimers.current.push(window.setTimeout(() => appendLog("Transcribing (AssemblyAI)…"), 1200))
    stageTimers.current.push(window.setTimeout(() => appendLog("Analyzing with AI Judge…"), 12000))
    stageTimers.current.push(window.setTimeout(() => appendLog("Scoring & weighing…"), 18000))
    stageTimers.current.push(window.setTimeout(() => appendLog("Writing RFD & flow…"), 23000))

    // smoothly tick up to ~89% max (avoid hitting 100 before server returns)
    tickerRef.current = window.setInterval(() => {
      setProgress((p) => {
        const inc = p < 55 ? 1.6 : p < 72 ? 1.1 : p < 82 ? 0.7 : p < 89 ? 0.4 : 0
        return Math.min(p + inc, 89)
      })
      return
    }, 500)
  }

  function stopTicker(finalTo100 = false) {
    if (tickerRef.current) {
      clearInterval(tickerRef.current)
      tickerRef.current = null
    }
    stageTimers.current.forEach(clearTimeout)
    stageTimers.current = []
    if (finalTo100) setProgress(100)
  }

  /* -------------------------   ANALYSIS   ---------------------------- */
  async function runDebate() {
    try {
      if (!file) return toast.error("Choose an audio file first")
      if (!canNext) return toast.error("Enter valid API keys")

      // reset
      setJob("running")
      setProgress(3)
      setLogs([])
      setLastResult(null)

      startTicker()

      const form = new FormData()
      form.append("file", file)
      form.append("aai_key", apiKeys.assemblyai)
      form.append("or_key", apiKeys.openrouter)
      form.append("topic", debateMeta.topic || "N/A")
      form.append("style", debateMeta.style)
      form.append("first", debateMeta.first)
      form.append("model", "openai/gpt-4o-2024-11-20")

      const data = await postForm("/api/analyze?type=debate", form)

      stopTicker(true)
      appendLog("Completed ✓")

      // persist for results page and keep local copy
      localStorage.setItem("vocius_last_result", JSON.stringify(data))
      setLastResult(data)

      setJob("done")
      ding()
      try { document.title = "Vocius — Debate ready ✓" } catch {}
    } catch (err: any) {
      stopTicker(false)
      setJob("error")
      setProgress(0)
      const msg = err?.message || "Analysis failed"
      appendLog(`Error: ${msg}`)
      toast.error(msg)
    }
  }

  function openResultsInNewTab() {
    const tab = window.open("/results", "_blank", "noopener,noreferrer")
    if (!tab) toast.error("Pop-up blocked. Allow pop-ups for localhost to see results.")
  }

  /* ===================================================================== */
  /*                                RENDER                                 */
  /* ===================================================================== */
  return (
    <div className="min-h-screen pt-12 relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="pointer-events-none absolute inset-0 -z-10">
        <div className="absolute -top-40 -left-32 h-[36rem] w-[36rem] rounded-full bg-orange-200/30 blur-3xl animate-pulse" />
        <div className="absolute -bottom-48 -right-40 h-[44rem] w-[44rem] rounded-full bg-indigo-200/30 blur-3xl animate-[pulse_8s_ease-in-out_infinite]" />
      </div>

      {/* Header */}
      <header className="text-center mb-8">
        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl font-bold text-gray-900"
        >
          From Upload to Victory — <span className="text-vocius-orange">Vocius</span>
        </motion.h1>
        <p className="text-lg text-gray-600 mt-2">
          Upload your debate for instant AI judging and feedback
        </p>
      </header>

      <div className="container mx-auto px-4 pb-16 max-w-5xl space-y-6">
        {/* STEP 1: API KEYS */}
        {step === 1 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="w-5 h-5" />
                API Keys
              </CardTitle>
              <CardDescription>Enter your credentials to enable analysis</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <Label>AssemblyAI</Label>
                <Input
                  type="password"
                  placeholder="ASSEMBLYAI_API_KEY"
                  value={apiKeys.assemblyai}
                  onChange={(e) => setApiKeys({ ...apiKeys, assemblyai: e.target.value.trim() })}
                />
                <p className={`text-sm ${aaiOk ? "text-green-600" : "text-gray-500"}`}>
                  {aaiOk ? "Looks good ✓" : "Required"}
                </p>
              </div>
              <div className="space-y-2">
                <Label>OpenRouter (for the judge)</Label>
                <Input
                  type="password"
                  placeholder="OPENROUTER_API_KEY"
                  value={apiKeys.openrouter}
                  onChange={(e) => setApiKeys({ ...apiKeys, openrouter: e.target.value.trim() })}
                />
                <p className={`text-sm ${orOk ? "text-green-600" : "text-gray-500"}`}>
                  {orOk ? "Looks good ✓" : "Required"}
                </p>
              </div>

              <div className="pt-2">
                <Button
                  className="bg-vocius-orange hover:bg-vocius-orange-hover"
                  disabled={!canNext}
                  onClick={() => setStep(2)}
                >
                  Next
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* STEP 2: ANALYZE (single screen) */}
        {step === 2 && (
          <>
            {/* Event + Meta */}
            <div className="grid md:grid-cols-3 gap-6">
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5" />
                    Setup
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Event (locked to PF for now) */}
                  <div className="space-y-2">
                    <Label>Event</Label>
                    <div className="relative">
                      <select
                        className="w-full appearance-none rounded-md border border-gray-300 bg-white px-3 py-2 pr-10 text-gray-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-vocius-orange"
                        value="pf"
                        onChange={() => {}}
                      >
                        <option value="pf">✓ Public Forum</option>
                      </select>
                      <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">▾</span>
                    </div>
                  </div>

                  {/* Topic */}
                  <div className="space-y-2">
                    <Label>Resolution / Topic</Label>
                    <Input
                      placeholder="Resolved: The United States should …"
                      value={debateMeta.topic}
                      onChange={(e) =>
                        setDebateMeta({ ...debateMeta, topic: e.target.value })
                      }
                    />
                  </div>

                  {/* First + Style */}
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Who speaks first?</Label>
                      <div className="flex items-center gap-6">
                        {["Aff", "Neg"].map((side) => (
                          <label key={side} className="flex items-center gap-2 cursor-pointer">
                            <input
                              type="radio"
                              name="first"
                              value={side}
                              checked={debateMeta.first === side}
                              onChange={() =>
                                setDebateMeta({ ...debateMeta, first: side })
                              }
                            />
                            {side}
                          </label>
                        ))}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Label>Judge Style</Label>
                      <div className="relative">
                        <select
                          className="w-full appearance-none rounded-md border border-gray-300 bg-white px-3 py-2 pr-10 text-gray-800 shadow-sm focus:outline-none focus:ring-2 focus:ring-vocius-orange"
                          value={debateMeta.style}
                          onChange={(e) =>
                            setDebateMeta({ ...debateMeta, style: e.target.value })
                          }
                        >
                          <option value="tech">Tech</option>
                          <option value="lay">Lay</option>
                          <option value="flay">Flay</option>
                          <option value="prog">Prog</option>
                        </select>
                        <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400">▾</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Speech Metrics (promo) */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-vocius-orange" />
                    <span>Speech Metrics (Delivery)</span>
                    <span className="ml-2 rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-800">
                      New
                    </span>
                  </CardTitle>
                  <CardDescription>
                    After your debate finishes, boost delivery with{" "}
                    <span className="font-semibold">pace, pauses, clarity, pitch-range</span> and more.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    variant="secondary"
                    className="w-full"
                    disabled={job !== "done"}
                    onClick={() => router.push("/playground")} // placeholder action
                  >
                    Try Speech Metrics (Beta)
                  </Button>
                  {job !== "done" && (
                    <p className="mt-2 text-xs text-gray-500">
                      Available after your debate analysis completes.
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Upload */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload Audio
                </CardTitle>
                <CardDescription>Drag & drop .m4a / .wav or click to browse</CardDescription>
              </CardHeader>
              <CardContent>
                <motion.label
                  htmlFor="file"
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  className={`block rounded-lg p-8 text-center cursor-pointer transition-all border-2 border-dashed ${
                    dragActive
                      ? "border-orange-400 bg-orange-50"
                      : file
                      ? "border-emerald-400 bg-emerald-50"
                      : "border-gray-300 hover:border-orange-300"
                  }`}
                  whileHover={{ scale: 1.01 }}
                >
                  {file ? (
                    <>
                      <Mic className="w-6 h-6 text-emerald-600 mx-auto mb-2" />
                      <p className="font-medium">{file.name}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {(file.size / 1_048_576).toFixed(2)} MB — click to replace
                      </p>
                    </>
                  ) : (
                    <>
                      <Upload className="w-6 h-6 text-gray-400 mx-auto mb-2" />
                      <p>Drop your audio here or click to browse</p>
                    </>
                  )}
                </motion.label>
                <input
                  id="file"
                  className="hidden"
                  type="file"
                  accept=".m4a,.wav,audio/*"
                  onChange={handleFilePick}
                />
              </CardContent>
            </Card>

            {/* Action + Progress */}
            <div className="grid md:grid-cols-2 gap-6">
              <Card>
                <CardContent className="pt-6">
                  {job !== "done" ? (
                    <Button
                      className="w-full bg-vocius-orange hover:bg-vocius-orange-hover"
                      disabled={!canAnalyze || job === "running"}
                      onClick={runDebate}
                    >
                      {job === "running" ? "Running…" : "Run Vocius Judge"}
                    </Button>
                  ) : (
                    <Button
                      className="w-full bg-vocius-orange hover:bg-vocius-orange-hover"
                      onClick={openResultsInNewTab}
                    >
                      View Debate Results
                    </Button>
                  )}

                  {job === "done" && (
                    <p className="mt-3 text-center text-green-700 font-medium">Completed ✓</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Clock className="w-5 h-5" />
                    Progress
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1">
                    <div className="flex justify-between text-sm">
                      <span>Debate</span>
                      <span>{Math.round(progress)}%</span>
                    </div>
                    <Progress value={progress} />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Console */}
            <Card>
              <CardHeader>
                <CardTitle>Console</CardTitle>
              </CardHeader>
              <CardContent>
                <pre className="bg-black text-green-400 p-4 rounded-lg font-mono text-sm h-56 overflow-y-auto whitespace-pre-wrap">
{logs.join("\n") || "Waiting…"}
                </pre>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  )
}
