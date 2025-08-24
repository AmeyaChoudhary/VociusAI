"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Check, X, Star, Users, Zap, Shield } from "lucide-react"

const pricingTiers = [
  {
    name: "Free Trial",
    price: "$0",
    period: "7 days",
    description: "Perfect for trying out Vocius",
    features: [
      { name: "3 analysis sessions", included: true },
      { name: "Basic feedback reports", included: true },
      { name: "Email support", included: true },
      { name: "Performance tracking", included: false },
      { name: "Advanced coaching insights", included: false },
      { name: "Team collaboration", included: false },
      { name: "Priority support", included: false },
      { name: "Export reports", included: false },
    ],
    cta: "Start Free Trial",
    popular: false,
    icon: Zap,
    color: "gray",
  },
  {
    name: "Pro",
    price: "$9",
    period: "month",
    description: "For serious debaters and competitors",
    features: [
      { name: "Unlimited analysis sessions", included: true },
      { name: "Advanced coaching insights", included: true },
      { name: "Performance tracking", included: true },
      { name: "Priority support", included: true },
      { name: "Export reports (PDF/TXT)", included: true },
      { name: "Historical data access", included: true },
      { name: "Team collaboration", included: false },
      { name: "Coach dashboard", included: false },
    ],
    cta: "Get Pro",
    popular: true,
    icon: Star,
    color: "orange",
  },
  {
    name: "Team",
    price: "$29",
    period: "month",
    description: "For debate teams and coaches",
    features: [
      { name: "Everything in Pro", included: true },
      { name: "Team collaboration tools", included: true },
      { name: "Coach dashboard", included: true },
      { name: "Bulk analysis processing", included: true },
      { name: "Custom integrations", included: true },
      { name: "Advanced analytics", included: true },
      { name: "White-label reports", included: true },
      { name: "Dedicated support", included: true },
    ],
    cta: "Contact Sales",
    popular: false,
    icon: Users,
    color: "blue",
  },
]

const additionalFeatures = [
  {
    icon: Shield,
    title: "Enterprise Security",
    description: "SOC 2 compliant with end-to-end encryption",
  },
  {
    icon: Zap,
    title: "Lightning Fast",
    description: "Analysis results in under 60 seconds",
  },
  {
    icon: Users,
    title: "Expert Support",
    description: "Get help from debate coaches and AI experts",
  },
]

export function PricingCards() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "yearly">("monthly")

  return (
    <div className="space-y-16">
      {/* Billing Toggle */}
      <div className="flex justify-center">
        <div className="flex items-center gap-4 p-1 bg-gray-100 rounded-lg">
          <button
            onClick={() => setBillingCycle("monthly")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              billingCycle === "monthly"
                ? "bg-white text-vocius-text shadow-sm"
                : "text-gray-600 hover:text-vocius-text"
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle("yearly")}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
              billingCycle === "yearly" ? "bg-white text-vocius-text shadow-sm" : "text-gray-600 hover:text-vocius-text"
            }`}
          >
            Yearly
            <Badge className="ml-2 bg-vocius-orange text-white text-xs">Save 20%</Badge>
          </button>
        </div>
      </div>

      {/* Pricing Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-7xl mx-auto">
        {pricingTiers.map((tier, index) => (
          <motion.div
            key={tier.name}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
              duration: 0.6,
              delay: index * 0.1,
              ease: "easeOut",
            }}
            whileHover={{ y: -8 }}
            className="relative group"
          >
            {tier.popular && (
              <motion.div
                animate={{ scale: [1, 1.05, 1] }}
                transition={{ duration: 2, repeat: Number.POSITIVE_INFINITY }}
                className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-vocius-orange text-white px-6 py-2 rounded-full text-sm font-semibold shadow-lg z-10"
              >
                Most Popular
              </motion.div>
            )}

            <Card
              className={`h-full transition-all duration-300 border-0 shadow-lg ${
                tier.popular
                  ? "ring-2 ring-vocius-orange shadow-vocius-orange/20 group-hover:shadow-vocius-orange/30"
                  : "shadow-gray-200 group-hover:shadow-gray-300"
              } group-hover:shadow-xl`}
            >
              <CardHeader className="text-center pb-4">
                <div className="flex justify-center mb-4">
                  <div
                    className={`w-16 h-16 rounded-full flex items-center justify-center ${
                      tier.popular ? "bg-vocius-orange/10" : "bg-gray-100"
                    }`}
                  >
                    <tier.icon className={`w-8 h-8 ${tier.popular ? "text-vocius-orange" : "text-gray-600"}`} />
                  </div>
                </div>

                <CardTitle className="font-sans text-2xl font-bold text-vocius-text mb-2">{tier.name}</CardTitle>

                <div className="mb-4">
                  <span className="text-5xl font-bold text-vocius-text">
                    {billingCycle === "yearly" && tier.price !== "$0"
                      ? `$${Math.round(Number.parseInt(tier.price.slice(1)) * 0.8)}`
                      : tier.price}
                  </span>
                  <span className="text-muted-foreground text-lg">
                    /{billingCycle === "yearly" && tier.price !== "$0" ? "month" : tier.period}
                  </span>
                  {billingCycle === "yearly" && tier.price !== "$0" && (
                    <div className="text-sm text-muted-foreground mt-1">
                      Billed annually (${Number.parseInt(tier.price.slice(1)) * 0.8 * 12}/year)
                    </div>
                  )}
                </div>

                <p className="text-muted-foreground">{tier.description}</p>
              </CardHeader>

              <CardContent className="pt-0">
                <ul className="space-y-4 mb-8">
                  {tier.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start gap-3">
                      {feature.included ? (
                        <Check className="w-5 h-5 text-vocius-orange flex-shrink-0 mt-0.5" />
                      ) : (
                        <X className="w-5 h-5 text-gray-300 flex-shrink-0 mt-0.5" />
                      )}
                      <span className={`text-sm ${feature.included ? "text-gray-700" : "text-gray-400 line-through"}`}>
                        {feature.name}
                      </span>
                    </li>
                  ))}
                </ul>

                <Button
                  className={`w-full py-3 text-lg font-semibold transition-all duration-300 ${
                    tier.popular
                      ? "bg-vocius-orange hover:bg-vocius-orange/90 text-white shadow-lg hover:shadow-xl"
                      : "bg-gray-900 hover:bg-gray-800 text-white"
                  }`}
                >
                  {tier.cta}
                </Button>

                {tier.name === "Team" && (
                  <p className="text-center text-sm text-muted-foreground mt-3">
                    Custom pricing available for large teams
                  </p>
                )}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Additional Features */}
      <div className="bg-vocius-gray py-16 -mx-4 px-4 rounded-2xl">
        <div className="text-center mb-12">
          <h3 className="font-sans text-3xl font-bold text-vocius-text mb-4">Why Choose Vocius?</h3>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Built by debate experts, powered by cutting-edge AI technology
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          {additionalFeatures.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.8 + index * 0.1 }}
              className="text-center"
            >
              <div className="w-16 h-16 bg-vocius-orange/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <feature.icon className="w-8 h-8 text-vocius-orange" />
              </div>
              <h4 className="font-sans text-xl font-semibold text-vocius-text mb-2">{feature.title}</h4>
              <p className="text-muted-foreground">{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>

      {/* FAQ Section */}
      <div className="max-w-3xl mx-auto">
        <h3 className="font-sans text-3xl font-bold text-center text-vocius-text mb-12">Frequently Asked Questions</h3>

        <div className="space-y-6">
          {[
            {
              question: "Can I switch plans anytime?",
              answer:
                "Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and we'll prorate any billing adjustments.",
            },
            {
              question: "What audio formats do you support?",
              answer:
                "We support .m4a, .wav, and .mp3 files. For best results, we recommend high-quality recordings with minimal background noise.",
            },
            {
              question: "How accurate is the AI analysis?",
              answer:
                "Our AI models are trained on thousands of debate rounds and achieve 95%+ accuracy in transcription and argument analysis. Results improve with audio quality.",
            },
            {
              question: "Do you offer refunds?",
              answer:
                "We offer a 30-day money-back guarantee for all paid plans. If you're not satisfied, contact us for a full refund.",
            },
          ].map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 1.2 + index * 0.1 }}
            >
              <Card className="border-0 shadow-sm">
                <CardContent className="p-6">
                  <h4 className="font-semibold text-vocius-text mb-2">{faq.question}</h4>
                  <p className="text-muted-foreground">{faq.answer}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>

      {/* CTA Section */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 1.6 }}
        className="text-center bg-gradient-to-r from-vocius-orange/10 to-vocius-orange/5 py-16 px-8 rounded-2xl"
      >
        <h3 className="font-sans text-3xl font-bold text-vocius-text mb-4">Ready to Elevate Your Debate Skills?</h3>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
          Unlock your entire potential with Vocius Pro.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button
            size="lg"
            className="bg-vocius-orange hover:bg-vocius-orange/90 text-white px-8 py-3 text-lg font-semibold"
          >
            Upgrade
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="border-vocius-orange text-vocius-orange hover:bg-vocius-orange hover:text-white px-8 py-3 text-lg font-semibold bg-transparent"
          >
            Schedule Demo
          </Button>
        </div>
        <p className="text-sm text-muted-foreground mt-6">
          If you're a coach or team manager contact us at ameya.jairam.choudhary@gmail.com for more info on the Team
          subscription
        </p>
      </motion.div>
    </div>
  )
}
