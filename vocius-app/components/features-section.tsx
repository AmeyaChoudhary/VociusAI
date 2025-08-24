"use client"

import { useRef } from "react"
import { motion, useInView } from "framer-motion"
import { Card, CardContent } from "@/components/ui/card"
import { Zap, Target, BarChart3, Users, Clock, Shield } from "lucide-react"

const features = [
  {
    icon: Zap,
    title: "Real-time Analysis",
    description: "Get instant feedback on your debate performance with our advanced AI algorithms",
  },
  {
    icon: Target,
    title: "Precision Coaching",
    description: "Targeted suggestions to improve your argumentation and delivery techniques",
  },
  {
    icon: BarChart3,
    title: "Performance Metrics",
    description: "Track your progress with detailed analytics on pace, pauses, and pitch variation",
  },
  {
    icon: Users,
    title: "Team Collaboration",
    description: "Share results with coaches and teammates for collaborative improvement",
  },
  {
    icon: Clock,
    title: "Time Efficiency",
    description: "Save hours of manual review with automated transcription and analysis",
  },
  {
    icon: Shield,
    title: "Secure & Private",
    description: "Your recordings and data are protected with enterprise-grade security",
  },
]

export function FeaturesSection() {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  return (
    <section ref={ref} className="py-20 relative overflow-hidden">
      {/* Animated background with floating gradient blobs */}
      <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-orange-50/30 to-indigo-50/20">
        <motion.div
          className="absolute top-10 right-20 w-72 h-72 bg-gradient-to-r from-vocius-orange/15 to-yellow-300/15 rounded-full blur-3xl"
          animate={{
            x: [0, -60, 0],
            y: [0, 50, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 12,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-10 left-20 w-64 h-64 bg-gradient-to-r from-purple-300/15 to-vocius-orange/15 rounded-full blur-3xl"
          animate={{
            x: [0, 40, 0],
            y: [0, -30, 0],
            scale: [1, 0.8, 1],
          }}
          transition={{
            duration: 9,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute top-1/3 left-1/3 w-48 h-48 bg-gradient-to-r from-indigo-300/10 to-pink-300/10 rounded-full blur-2xl"
          animate={{
            x: [0, 20, -20, 0],
            y: [0, -40, 40, 0],
            rotate: [0, 90, 180, 270, 360],
          }}
          transition={{
            duration: 20,
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
          <h2 className="font-sans text-4xl font-bold text-vocius-text mb-4">Powerful Features</h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Everything you need to elevate your debate skills and achieve victory
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 50 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
              transition={{
                duration: 0.6,
                delay: index * 0.1,
                ease: "easeOut",
              }}
              whileHover={{ y: -4 }}
              className="group"
            >
              <Card className="h-full hover:shadow-xl transition-all duration-300 border-0 shadow-md hover:shadow-vocius-orange/40 hover:ring-2 hover:ring-vocius-orange/30 group-hover:bg-gradient-to-br group-hover:from-white group-hover:to-orange-50/20">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-vocius-orange/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-vocius-orange/30 group-hover:shadow-lg group-hover:shadow-vocius-orange/20 transition-all duration-300">
                    <feature.icon className="w-6 h-6 text-vocius-orange group-hover:scale-110 transition-transform duration-300" />
                  </div>
                  <h3 className="font-sans text-xl font-semibold text-vocius-text mb-3">{feature.title}</h3>
                  <p className="text-muted-foreground leading-relaxed">{feature.description}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
