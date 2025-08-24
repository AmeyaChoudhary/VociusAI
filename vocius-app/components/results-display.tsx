"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Download, FileText, BarChart3, Clock, Volume2, Zap } from "lucide-react"

// Mock data - replace with real API data later
const mockResults = {
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
        notes: "Topicality shell. Disadvantage: spending leads to inflation. Counterplan: private sector alternative.",
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

export function ResultsDisplay() {
  const [activeTab, setActiveTab] = useState<"judge" | "delivery">("judge")

  const downloadReport = (type: "judge" | "delivery") => {
    const content =
      type === "judge"
        ? `JUDGE ANALYSIS REPORT\n\nOverall Score: ${mockResults.judgeAnalysis.overallScore}/100\n\nReason for Decision:\n${mockResults.judgeAnalysis.rfd}\n\nFlow Notes:\n${mockResults.judgeAnalysis.flowNotes.map((note) => `${note.speech} (${note.time}): ${note.notes}`).join("\n\n")}\n\nVerdict: ${mockResults.judgeAnalysis.verdict}`
        : `DELIVERY METRICS REPORT\n\nOverall Score: ${mockResults.deliveryMetrics.overallScore}/100\n\nPace Analysis:\nAverage WPM: ${mockResults.deliveryMetrics.pace.averageWpm}\nOptimal Range: ${mockResults.deliveryMetrics.pace.optimalRange}\nScore: ${mockResults.deliveryMetrics.pace.score}/100\nAnalysis: ${mockResults.deliveryMetrics.pace.analysis}\n\nPauses Analysis:\nTotal Pauses: ${mockResults.deliveryMetrics.pauses.totalPauses}\nAverage Length: ${mockResults.deliveryMetrics.pauses.averageLength}s\nScore: ${mockResults.deliveryMetrics.pauses.score}/100\nAnalysis: ${mockResults.deliveryMetrics.pauses.analysis}\n\nPitch Range Analysis:\nRange: ${mockResults.deliveryMetrics.pitchRange.range}\nVariation: ${mockResults.deliveryMetrics.pitchRange.variation}\nScore: ${mockResults.deliveryMetrics.pitchRange.score}/100\nAnalysis: ${mockResults.deliveryMetrics.pitchRange.analysis}`

    const blob = new Blob([content], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `vocius-${type}-report.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6">
      {/* Overall Scores */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-vocius-orange/10 rounded-lg flex items-center justify-center">
                  <FileText className="w-5 h-5 text-vocius-orange" />
                </div>
                <div>
                  <h3 className="font-serif text-lg font-semibold">Judge Analysis</h3>
                  <p className="text-sm text-muted-foreground">Argument evaluation</p>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Overall Score</span>
                  <Badge variant="secondary" className="bg-vocius-orange/10 text-vocius-orange">
                    {mockResults.judgeAnalysis.overallScore}/100
                  </Badge>
                </div>
                <Progress value={mockResults.judgeAnalysis.overallScore} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 bg-vocius-orange/10 rounded-lg flex items-center justify-center">
                  <BarChart3 className="w-5 h-5 text-vocius-orange" />
                </div>
                <div>
                  <h3 className="font-serif text-lg font-semibold">Delivery Metrics</h3>
                  <p className="text-sm text-muted-foreground">Speech performance</p>
                </div>
              </div>
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-sm font-medium">Overall Score</span>
                  <Badge variant="secondary" className="bg-vocius-orange/10 text-vocius-orange">
                    {mockResults.deliveryMetrics.overallScore}/100
                  </Badge>
                </div>
                <Progress value={mockResults.deliveryMetrics.overallScore} className="h-2" />
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Tab Navigation */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => setActiveTab("judge")}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "judge"
              ? "border-vocius-orange text-vocius-orange"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Judge Analysis
        </button>
        <button
          onClick={() => setActiveTab("delivery")}
          className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
            activeTab === "delivery"
              ? "border-vocius-orange text-vocius-orange"
              : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          Delivery Metrics
        </button>
      </div>

      {/* Content Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {activeTab === "judge" ? (
          <>
            {/* Judge Feedback Panel */}
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
              <Card className="h-fit">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="font-serif text-xl">Reason for Decision</CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => downloadReport("judge")}
                    className="border-vocius-orange text-vocius-orange hover:bg-vocius-orange hover:text-white bg-transparent"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download .txt
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <pre className="whitespace-pre-wrap text-sm leading-relaxed text-gray-700 font-sans">
                      {mockResults.judgeAnalysis.rfd}
                    </pre>
                  </div>
                  <div className="mt-6 p-4 bg-vocius-orange/5 rounded-lg border border-vocius-orange/20">
                    <h4 className="font-semibold text-vocius-orange mb-2">Verdict</h4>
                    <p className="text-sm">{mockResults.judgeAnalysis.verdict}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Flow Notes Panel */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Card className="h-fit">
                <CardHeader>
                  <CardTitle className="font-serif text-xl">Flow Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {mockResults.judgeAnalysis.flowNotes.map((note, index) => (
                      <div key={index} className="border-l-4 border-vocius-orange/30 pl-4">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge variant="outline" className="text-xs">
                            {note.speech}
                          </Badge>
                          <span className="text-xs text-muted-foreground">{note.time}</span>
                        </div>
                        <p className="text-sm text-gray-700">{note.notes}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </>
        ) : (
          <>
            {/* Delivery Metrics Panel */}
            <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5 }}>
              <Card className="h-fit">
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="font-serif text-xl">Performance Metrics</CardTitle>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => downloadReport("delivery")}
                    className="border-vocius-orange text-vocius-orange hover:bg-vocius-orange hover:text-white bg-transparent"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download .txt
                  </Button>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Pace */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Clock className="w-4 h-4 text-vocius-orange" />
                      <h4 className="font-semibold">Pace Analysis</h4>
                      <Badge variant="secondary" className="ml-auto">
                        {mockResults.deliveryMetrics.pace.score}/100
                      </Badge>
                    </div>
                    <Progress value={mockResults.deliveryMetrics.pace.score} className="h-2 mb-2" />
                    <div className="text-sm space-y-1">
                      <p>
                        <strong>Average WPM:</strong> {mockResults.deliveryMetrics.pace.averageWpm}
                      </p>
                      <p>
                        <strong>Optimal Range:</strong> {mockResults.deliveryMetrics.pace.optimalRange}
                      </p>
                      <p className="text-muted-foreground">{mockResults.deliveryMetrics.pace.analysis}</p>
                    </div>
                  </div>

                  {/* Pauses */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Zap className="w-4 h-4 text-vocius-orange" />
                      <h4 className="font-semibold">Pause Analysis</h4>
                      <Badge variant="secondary" className="ml-auto">
                        {mockResults.deliveryMetrics.pauses.score}/100
                      </Badge>
                    </div>
                    <Progress value={mockResults.deliveryMetrics.pauses.score} className="h-2 mb-2" />
                    <div className="text-sm space-y-1">
                      <p>
                        <strong>Total Pauses:</strong> {mockResults.deliveryMetrics.pauses.totalPauses}
                      </p>
                      <p>
                        <strong>Average Length:</strong> {mockResults.deliveryMetrics.pauses.averageLength}s
                      </p>
                      <p className="text-muted-foreground">{mockResults.deliveryMetrics.pauses.analysis}</p>
                    </div>
                  </div>

                  {/* Pitch Range */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <Volume2 className="w-4 h-4 text-vocius-orange" />
                      <h4 className="font-semibold">Pitch Range</h4>
                      <Badge variant="secondary" className="ml-auto">
                        {mockResults.deliveryMetrics.pitchRange.score}/100
                      </Badge>
                    </div>
                    <Progress value={mockResults.deliveryMetrics.pitchRange.score} className="h-2 mb-2" />
                    <div className="text-sm space-y-1">
                      <p>
                        <strong>Range:</strong> {mockResults.deliveryMetrics.pitchRange.range}
                      </p>
                      <p>
                        <strong>Variation:</strong> {mockResults.deliveryMetrics.pitchRange.variation}
                      </p>
                      <p className="text-muted-foreground">{mockResults.deliveryMetrics.pitchRange.analysis}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Additional Metrics Panel */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <Card className="h-fit">
                <CardHeader>
                  <CardTitle className="font-serif text-xl">Additional Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Clarity */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold">Clarity</h4>
                      <Badge variant="secondary">{mockResults.deliveryMetrics.clarity.score}/100</Badge>
                    </div>
                    <Progress value={mockResults.deliveryMetrics.clarity.score} className="h-2 mb-2" />
                    <p className="text-sm text-muted-foreground">{mockResults.deliveryMetrics.clarity.analysis}</p>
                  </div>

                  {/* Volume */}
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-semibold">Volume Control</h4>
                      <Badge variant="secondary">{mockResults.deliveryMetrics.volume.score}/100</Badge>
                    </div>
                    <Progress value={mockResults.deliveryMetrics.volume.score} className="h-2 mb-2" />
                    <p className="text-sm text-muted-foreground">{mockResults.deliveryMetrics.volume.analysis}</p>
                  </div>

                  {/* Summary */}
                  <div className="p-4 bg-vocius-orange/5 rounded-lg border border-vocius-orange/20">
                    <h4 className="font-semibold text-vocius-orange mb-2">Key Recommendations</h4>
                    <ul className="text-sm space-y-1 text-gray-700">
                      <li>• Practice maintaining consistent pace during rebuttals</li>
                      <li>• Reduce filler pauses between major arguments</li>
                      <li>• Project voice more during cross-examination</li>
                      <li>• Continue excellent use of vocal variety for emphasis</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          </>
        )}
      </div>
    </div>
  )
}
