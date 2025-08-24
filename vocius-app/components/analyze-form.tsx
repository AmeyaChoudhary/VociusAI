"use client"

import type React from "react"

import { useState, useCallback } from "react"
import { motion } from "framer-motion"
import { useDropzone } from "react-dropzone"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { Upload, FileAudio, X, Play } from "lucide-react"
import { useRouter } from "next/navigation"

interface AnalysisLog {
  timestamp: string
  message: string
  type: "info" | "success" | "error"
}

export function AnalyzeForm() {
  const router = useRouter()
  const [file, setFile] = useState<File | null>(null)
  const [apiKeys, setApiKeys] = useState({
    openai: "",
    huggingface: "",
    openrouter: "",
  })
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [judgingProgress, setJudgingProgress] = useState(0)
  const [deliveryProgress, setDeliveryProgress] = useState(0)
  const [logs, setLogs] = useState<AnalysisLog[]>([])

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const audioFile = acceptedFiles[0]
    if (audioFile) {
      setFile(audioFile)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "audio/*": [".m4a", ".wav", ".mp3"],
    },
    maxFiles: 1,
  })

  const addLog = (message: string, type: AnalysisLog["type"] = "info") => {
    const newLog: AnalysisLog = {
      timestamp: new Date().toLocaleTimeString(),
      message,
      type,
    }
    setLogs((prev) => [...prev, newLog])
  }

  const simulateAnalysis = async () => {
    setIsAnalyzing(true)
    setJudgingProgress(0)
    setDeliveryProgress(0)
    setLogs([])

    // Simulate analysis process
    addLog("Starting analysis...", "info")
    addLog("Uploading audio file...", "info")

    // Simulate judging progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise((resolve) => setTimeout(resolve, 200))
      setJudgingProgress(i)
      if (i === 30) addLog("Transcribing audio...", "info")
      if (i === 60) addLog("Analyzing arguments...", "info")
      if (i === 90) addLog("Generating judge feedback...", "info")
    }

    addLog("Judging analysis complete!", "success")

    // Simulate delivery progress
    for (let i = 0; i <= 100; i += 15) {
      await new Promise((resolve) => setTimeout(resolve, 150))
      setDeliveryProgress(i)
      if (i === 30) addLog("Analyzing speech patterns...", "info")
      if (i === 60) addLog("Measuring pace and pauses...", "info")
      if (i === 90) addLog("Calculating delivery metrics...", "info")
    }

    addLog("Delivery analysis complete!", "success")
    addLog("Analysis finished! Redirecting to results...", "success")

    // Redirect to results after a short delay
    setTimeout(() => {
      router.push("/results")
    }, 2000)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) {
      addLog("Please upload an audio file first", "error")
      return
    }
    if (!apiKeys.openai || !apiKeys.huggingface || !apiKeys.openrouter) {
      addLog("Please provide all required API keys", "error")
      return
    }
    simulateAnalysis()
  }

  const removeFile = () => {
    setFile(null)
  }

  return (
    <div className="space-y-8">
      {/* File Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="font-serif text-xl">Upload Audio File</CardTitle>
        </CardHeader>
        <CardContent>
          {!file ? (
            <motion.div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                isDragActive ? "border-vocius-orange bg-vocius-orange/5" : "border-gray-300 hover:border-vocius-orange"
              }`}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <input {...getInputProps()} />
              <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-700 mb-2">
                {isDragActive ? "Drop your audio file here" : "Drag & drop your audio file here"}
              </p>
              <p className="text-sm text-gray-500 mb-4">Supports .m4a, .wav, and .mp3 files</p>
              <Button
                type="button"
                variant="outline"
                className="border-vocius-orange text-vocius-orange bg-transparent"
              >
                Browse Files
              </Button>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-4 p-4 bg-vocius-orange/5 rounded-lg border border-vocius-orange/20"
            >
              <FileAudio className="w-8 h-8 text-vocius-orange" />
              <div className="flex-1">
                <p className="font-medium text-gray-900">{file.name}</p>
                <p className="text-sm text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={removeFile}>
                <X className="w-4 h-4" />
              </Button>
            </motion.div>
          )}
        </CardContent>
      </Card>

      {/* API Keys Section */}
      <Card>
        <CardHeader>
          <CardTitle className="font-serif text-xl">API Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label htmlFor="openai-key">OpenAI API Key</Label>
            <Input
              id="openai-key"
              type="password"
              placeholder="sk-..."
              value={apiKeys.openai}
              onChange={(e) => setApiKeys((prev) => ({ ...prev, openai: e.target.value }))}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="hf-token">Hugging Face Token</Label>
            <Input
              id="hf-token"
              type="password"
              placeholder="hf_..."
              value={apiKeys.huggingface}
              onChange={(e) => setApiKeys((prev) => ({ ...prev, huggingface: e.target.value }))}
              className="mt-1"
            />
          </div>
          <div>
            <Label htmlFor="openrouter-key">OpenRouter API Key</Label>
            <Input
              id="openrouter-key"
              type="password"
              placeholder="sk-or-..."
              value={apiKeys.openrouter}
              onChange={(e) => setApiKeys((prev) => ({ ...prev, openrouter: e.target.value }))}
              className="mt-1"
            />
          </div>
        </CardContent>
      </Card>

      {/* Analysis Progress */}
      {isAnalyzing && (
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="font-serif text-xl">Analysis Progress</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <Label>Judging Analysis</Label>
                  <span className="text-sm text-gray-500">{judgingProgress}%</span>
                </div>
                <Progress value={judgingProgress} className="h-3" />
              </div>
              <div>
                <div className="flex justify-between items-center mb-2">
                  <Label>Delivery Analysis</Label>
                  <span className="text-sm text-gray-500">{deliveryProgress}%</span>
                </div>
                <Progress value={deliveryProgress} className="h-3" />
              </div>
            </CardContent>
          </Card>

          {/* Live Log Console */}
          <Card>
            <CardHeader>
              <CardTitle className="font-serif text-xl">Analysis Log</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-gray-900 text-green-400 p-4 rounded-lg h-48 overflow-y-auto font-mono text-sm">
                {logs.map((log, index) => (
                  <div key={index} className="mb-1">
                    <span className="text-gray-500">[{log.timestamp}]</span>{" "}
                    <span
                      className={
                        log.type === "error"
                          ? "text-red-400"
                          : log.type === "success"
                            ? "text-green-400"
                            : "text-blue-400"
                      }
                    >
                      {log.message}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Submit Button */}
      <form onSubmit={handleSubmit}>
        <Button
          type="submit"
          size="lg"
          disabled={isAnalyzing}
          className="w-full bg-vocius-orange hover:bg-vocius-orange/90 text-white py-3 text-lg font-semibold"
        >
          {isAnalyzing ? (
            <>
              <Play className="w-5 h-5 mr-2 animate-spin" />
              Analyzing...
            </>
          ) : (
            "Start Analysis"
          )}
        </Button>
      </form>
    </div>
  )
}
