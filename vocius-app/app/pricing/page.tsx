import { PricingCards } from "@/components/pricing-cards"

export default function PricingPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="text-center mb-12">
        <h1 className="font-sans text-4xl font-bold mb-4">Simple, Transparent Pricing</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Choose the plan that fits your debate coaching needs
        </p>
      </div>
      <PricingCards />
    </div>
  )
}
