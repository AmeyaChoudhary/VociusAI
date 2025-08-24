"use client"

import { useRef } from "react"
import { motion, useInView } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Check } from "lucide-react"
import Link from "next/link"

const pricingTiers = [
  {
    name: "Free Trial",
    price: "$0",
    period: "7 days",
    description: "Perfect for trying out Vocius",
    features: ["3 analysis sessions", "Basic feedback reports", "Email support"],
    cta: "Start Free Trial",
    popular: false,
  },
  {
    name: "Pro",
    price: "$9",
    period: "month",
    description: "For serious debaters",
    features: [
      "Unlimited analysis",
      "Advanced coaching insights",
      "Performance tracking",
      "Priority support",
      "Export reports",
    ],
    cta: "Get Pro",
    popular: true,
  },
  {
    name: "Team",
    price: "$29",
    period: "month",
    description: "For debate teams and coaches",
    features: ["Everything in Pro", "Team collaboration", "Coach dashboard", "Bulk analysis", "Custom integrations"],
    cta: "Contact Sales",
    popular: false,
  },
]

export function PricingPreview() {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: "-100px" })

  return (
    <section ref={ref} className="py-20 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-white via-orange-50/20 to-purple-50/10">
        <motion.div
          className="absolute top-16 left-16 w-80 h-80 bg-gradient-to-r from-vocius-orange/10 to-yellow-300/10 rounded-full blur-3xl"
          animate={{
            x: [0, 70, 0],
            y: [0, -50, 0],
            scale: [1, 1.3, 1],
          }}
          transition={{
            duration: 14,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute bottom-16 right-16 w-96 h-96 bg-gradient-to-r from-purple-300/10 to-vocius-orange/10 rounded-full blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, 60, 0],
            scale: [1, 0.8, 1],
          }}
          transition={{
            duration: 11,
            repeat: Number.POSITIVE_INFINITY,
            ease: "easeInOut",
          }}
        />
        <motion.div
          className="absolute top-1/2 left-1/4 w-64 h-64 bg-gradient-to-r from-indigo-300/8 to-pink-300/8 rounded-full blur-2xl"
          animate={{
            x: [0, 30, -30, 0],
            y: [0, -25, 25, 0],
            rotate: [0, 120, 240, 360],
          }}
          transition={{
            duration: 18,
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
          <h2 className="font-sans text-4xl font-bold text-vocius-text mb-4">Choose Your Plan</h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            Start your journey to debate excellence with our flexible pricing options
          </p>
          <Button
            asChild
            variant="outline"
            className="border-vocius-orange text-vocius-orange hover:bg-vocius-orange hover:text-white bg-transparent hover:shadow-lg hover:shadow-vocius-orange/30 transition-all duration-300"
          >
            <Link href="/pricing">View All Plans</Link>
          </Button>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {pricingTiers.map((tier, index) => (
            <motion.div
              key={tier.name}
              initial={{ opacity: 0, y: 50 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
              transition={{
                duration: 0.6,
                delay: index * 0.1,
                ease: "easeOut",
              }}
              whileHover={{ y: -4 }}
              className="relative group"
            >
              {tier.popular && (
                <motion.div
                  animate={{ scale: [1, 1.05, 1] }}
                  transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY }}
                  className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-vocius-orange text-white px-4 py-1 rounded-full text-sm font-medium"
                >
                  Most Popular
                </motion.div>
              )}
              <Card
                className={`h-full hover:shadow-xl transition-all duration-300 border-0 shadow-md hover:shadow-vocius-orange/40 hover:ring-2 hover:ring-vocius-orange/30 group-hover:bg-gradient-to-br group-hover:from-white group-hover:to-orange-50/30 ${
                  tier.popular ? "ring-2 ring-vocius-orange" : ""
                }`}
              >
                <CardHeader className="text-center pb-4">
                  <CardTitle className="font-sans text-2xl font-bold text-vocius-text">{tier.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-4xl font-bold text-vocius-text">{tier.price}</span>
                    <span className="text-muted-foreground">/{tier.period}</span>
                  </div>
                  <p className="text-muted-foreground mt-2">{tier.description}</p>
                </CardHeader>
                <CardContent className="pt-0">
                  <ul className="space-y-3 mb-6">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-3">
                        <Check className="w-5 h-5 text-vocius-orange flex-shrink-0" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    className={`w-full hover:shadow-lg transition-all duration-300 ${
                      tier.popular
                        ? "bg-vocius-orange hover:bg-vocius-orange/90 hover:shadow-vocius-orange/40"
                        : "bg-gray-900 hover:bg-gray-800 hover:shadow-gray-800/40"
                    }`}
                  >
                    {tier.cta}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
