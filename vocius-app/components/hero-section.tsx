"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { motion, useMotionValue, useSpring, useTransform, useScroll } from "framer-motion"
import { Button } from "@/components/ui/button"
import { ChevronDown } from "lucide-react"
import Link from "next/link"

export function HeroSection() {
  const [showStageB, setShowStageB] = useState(false)
  const [highlightIndex, setHighlightIndex] = useState(0) // Start with Vocius highlighted
  const [animationComplete, setAnimationComplete] = useState(false)
  const mouseX = useMotionValue(0)
  const mouseY = useMotionValue(0)
  const { scrollY } = useScroll()

  const springX = useSpring(mouseX, { stiffness: 120, damping: 18 })
  const springY = useSpring(mouseY, { stiffness: 120, damping: 18 })

  const spotlightX = useTransform(springX, [0, 1], [0, 1])
  const spotlightY = useTransform(springY, [0, 1], [0, 1])

  const stageBLines = ["Debate.", "Vocius.", "Repeat."]

  useEffect(() => {
    const unsubscribe = scrollY.onChange((latest) => {
      setShowStageB(latest > 120)
    })
    return unsubscribe
  }, [scrollY])

  useEffect(() => {
    const interval = setInterval(() => {
      setHighlightIndex((prev) => (prev + 1) % 3)
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = e.currentTarget.getBoundingClientRect()
    mouseX.set((e.clientX - rect.left) / rect.width)
    mouseY.set((e.clientY - rect.top) / rect.height)
  }

  const PodiumSVG = () => (
    <svg width="120" height="120" viewBox="0 0 120 120" className="text-vocius-orange/30">
      <rect x="20" y="80" width="80" height="30" rx="4" fill="currentColor" />
      <rect x="30" y="70" width="60" height="10" rx="2" fill="currentColor" />
      <circle cx="60" cy="50" r="15" fill="currentColor" />
      <rect x="55" y="35" width="10" height="15" fill="currentColor" />
    </svg>
  )

  const LeftSpeakerFigure = () => {
    return (
      <img
        src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Screenshot%202025-08-20%20at%2011.11.08%E2%80%AFPM-zMCIUtHwdVTUohmmLVZad3fLW573Hh.png"
        alt="Professional speaker at podium"
        className="w-64 h-auto object-contain"
      />
    )
  }

  const SpeakerFigure = () => {
    return (
      <img
        src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Screenshot%202025-08-20%20at%2011.09.36%E2%80%AFPM-xYeCY9zE8W8GKDfH64mDZ2cGVvBYHX.png"
        alt="Professional speaker at podium"
        className="w-64 h-auto object-contain"
      />
    )
  }

  return (
    <>
      <section
        className="relative h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-gray-50 via-orange-50/30 to-indigo-50/20"
        onMouseMove={handleMouseMove}
      >
        <div className="absolute inset-0 overflow-hidden">
          <motion.div
            className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-orange-200/40 to-orange-300/30 rounded-full blur-3xl"
            animate={{
              x: [0, 100, 0],
              y: [0, -50, 0],
              scale: [1, 1.2, 1],
            }}
            transition={{
              duration: 20,
              repeat: Number.POSITIVE_INFINITY,
              ease: "easeInOut",
            }}
          />
          <motion.div
            className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-l from-indigo-300/35 to-purple-200/25 rounded-full blur-3xl"
            animate={{
              x: [0, -80, 0],
              y: [0, 80, 0],
              scale: [1, 0.8, 1],
            }}
            transition={{
              duration: 25,
              repeat: Number.POSITIVE_INFINITY,
              ease: "easeInOut",
            }}
          />
        </div>

        <motion.div
          className="absolute inset-0 opacity-10"
          style={{
            background: `radial-gradient(200px circle at ${spotlightX}% ${spotlightY}%, rgba(255, 181, 107, 0.3), transparent 70%)`,
          }}
        />

        <motion.div
          className="absolute left-8 top-1/2 transform -translate-y-1/2 hidden lg:block"
          animate={{
            y: [0, -10, 0],
            rotate: [0, 2, 0],
          }}
          transition={{
            duration: 4,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        >
          <LeftSpeakerFigure />
        </motion.div>

        <motion.div
          className="absolute right-8 top-1/2 transform -translate-y-1/2 hidden lg:block"
          animate={{
            y: [0, -10, 0],
            rotate: [0, 2, 0],
          }}
          transition={{
            duration: 4,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        >
          <SpeakerFigure />
        </motion.div>

        <div className="relative z-10 text-center max-w-3xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="mb-8"
          >
            <motion.h1 className="font-sans text-5xl md:text-7xl font-bold leading-tight mb-4">
              <span className="text-vocius-orange">Vocius</span>
            </motion.h1>
            <p className="text-2xl md:text-3xl font-light text-vocius-text/80 mb-8">Your AI Debate Coach</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4, ease: "easeOut" }}
            className="flex justify-center"
          >
            <Button
              asChild
              size="lg"
              className="bg-vocius-orange hover:bg-vocius-orange-hover text-white px-8 py-3 text-lg font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300"
            >
              <Link href="/login">Try Vocius Free</Link>
            </Button>
          </motion.div>
        </div>

        <motion.div
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2"
          animate={{ y: [0, 8, 0] }}
          transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
        >
          <ChevronDown className="w-6 h-6 text-vocius-text/60" />
        </motion.div>
      </section>

      <motion.section
        className="relative py-20 bg-gradient-to-br from-slate-50 via-orange-50/20 to-indigo-50/10 overflow-hidden"
        initial={{ opacity: 0 }}
        animate={{ opacity: showStageB ? 1 : 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="max-w-4xl mx-auto px-4 text-center">
          <div className="space-y-6">
            {stageBLines.map((line, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: showStageB ? 1 : 0, y: showStageB ? 0 : 20 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="relative"
              >
                <h2
                  className={`font-sans text-3xl md:text-5xl font-bold transition-colors duration-300 ${
                    highlightIndex === index ? "text-vocius-orange" : "text-vocius-text"
                  }`}
                >
                  {line}
                </h2>
                <motion.div
                  className="absolute inset-0 bg-vocius-orange/20 rounded-lg -z-10"
                  initial={{ scaleX: 0 }}
                  animate={{
                    scaleX: highlightIndex === index ? 1 : 0,
                    originX: 0,
                  }}
                  transition={{
                    duration: 0.8,
                    ease: "easeOut",
                  }}
                />
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>
    </>
  )
}
