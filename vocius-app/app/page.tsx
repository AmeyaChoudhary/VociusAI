/* -------------------------------------------------------------------------- */
/*  app/page.tsx – Animated home background, keeps your existing sections     */
/* -------------------------------------------------------------------------- */
"use client"

import { motion } from "framer-motion"

import { HeroSection } from "@/components/hero-section"
import { PipelineSection } from "@/components/pipeline-section"
import { FeaturesSection } from "@/components/features-section"
import { PricingPreview } from "@/components/pricing-preview"

export default function HomePage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-gradient-to-br from-orange-50 via-white to-cyan-50">
      {/* Animated color blobs (behind content) */}
      <motion.div
        className="pointer-events-none absolute -top-28 -left-24 h-80 w-80 rounded-full bg-orange-200/40 blur-3xl"
        animate={{ y: [0, 16, 0], x: [0, 24, 0], scale: [1, 1.07, 1] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="pointer-events-none absolute -bottom-32 -right-28 h-96 w-96 rounded-full bg-cyan-200/40 blur-3xl"
        animate={{ y: [0, -18, 0], x: [0, -18, 0], scale: [1.08, 1, 1.08] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="pointer-events-none absolute left-1/2 top-1/3 h-64 w-64 -translate-x-1/2 rounded-full bg-violet-200/30 blur-2xl"
        animate={{ rotate: [0, 18, -12, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* Page content stays above the animated background */}
      <div className="relative z-10">
        <HeroSection />
        <PipelineSection />
        <FeaturesSection />
        <PricingPreview />
      </div>
    </main>
  )
}
