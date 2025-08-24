"use client"

import { useEffect, useRef, useState } from "react"
import { motion, useInView } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Upload, FileText, Brain, MessageSquare, Zap } from "lucide-react"

const pipelineSteps = [
  {
    icon: Upload,
    title: "Upload",
    description: "Upload your debate recording in .m4a or .wav format",
  },
  {
    icon: FileText,
    title: "Transcribe",
    description: "AI converts your speech to text with high accuracy",
  },
  {
    icon: Brain,
    title: "Judge/Coach",
    description: "Advanced AI analyzes your arguments and delivery",
  },
  {
    icon: MessageSquare,
    title: "Feedback",
    description: "Receive detailed feedback and improvement suggestions",
  },
]

export function PipelineSection() {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (isInView) {
      const timer = setTimeout(() => {
        setProgress(100)
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [isInView])

  return (
    <section ref={ref} className="py-20 relative overflow-hidden">
      {/* Animated background with floating gradient blobs */}
      <div className="absolute inset-0 bg-gradient-to-br from-gray-50 via-orange-50/40 to-indigo-50/30">
        <motion.div
          className="absolute top-20 left-10 w-64 h-64 bg-gradient-to-r from-vocius-orange/20 to-pink-300/20 rounded-full blur-3xl"
          animate={{
            x: [0, 50, 0],
            y: [0, -30, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 8,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-20 right-10 w-80 h-80 bg-gradient-to-r from-indigo-300/20 to-vocius-orange/20 rounded-full blur-3xl"
          animate={{
            x: [0, -40, 0],
            y: [0, 40, 0],
            scale: [1, 0.9, 1],
          }}
          transition={{
            duration: 10,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute top-1/2 left-1/2 w-96 h-96 bg-gradient-to-r from-purple-300/15 to-orange-300/15 rounded-full blur-3xl"
          animate={{
            x: [0, 30, -30, 0],
            y: [0, -20, 20, 0],
            rotate: [0, 180, 360],
          }}
          transition={{
            duration: 15,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
      </div>

      <div className="container mx-auto px-4 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="text-center mb-16"
        >
          <h2 className="font-sans text-4xl font-bold text-vocius-text mb-4">How Vocius Works</h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Our AI-powered pipeline transforms your debate recordings into actionable insights
          </p>
        </motion.div>

        {/* Progress bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.8, delay: 0.2 }}
          className="mb-12"
        >
          <div className="w-full bg-gray-200 rounded-full h-2 mb-8">
            <motion.div
              className="bg-vocius-orange h-2 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 2, ease: "easeOut", delay: 0.5 }}
            />
          </div>
        </motion.div>

        {/* Pipeline steps */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {pipelineSteps.map((step, index) => (
            <motion.div
              key={step.title}
              initial={{ opacity: 0, y: 50 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
              transition={{
                duration: 0.6,
                delay: 0.2 + index * 0.1,
                ease: "easeOut",
              }}
            >
              <Card className="h-full hover:shadow-xl transition-all duration-300 hover:-translate-y-1 border-0 shadow-md hover:shadow-vocius-orange/30 hover:ring-2 hover:ring-vocius-orange/20">
                <CardContent className="p-6 text-center">
                  <div className="w-16 h-16 bg-vocius-orange/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <step.icon className="w-8 h-8 text-vocius-orange" />
                  </div>
                  <h3 className="font-sans text-xl font-semibold text-vocius-text mb-2">{step.title}</h3>
                  <p className="text-muted-foreground">{step.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Timing indicator with lightning bolt */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.8, delay: 1.2 }}
          className="text-center mt-12"
        >
          <div className="inline-flex items-center gap-2 bg-vocius-orange/10 px-6 py-3 rounded-full">
            <Zap className="w-5 h-5 text-vocius-orange" />
            <span className="font-sans font-semibold text-vocius-text">Complete analysis in &lt;1 minute</span>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
