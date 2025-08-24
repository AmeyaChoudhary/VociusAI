"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Menu, Lock, Heart, ChevronDown } from "lucide-react"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Home", href: "/" },
  { name: "Playground", href: "/playground" },
  { name: "Pricing", href: "/pricing" },
  { name: "Dashboard", href: "/dashboard", locked: true },
]

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Debate Captain @ Stanford",
    quote: "Vocius transformed my debate performance. The AI coaching insights are incredibly detailed and actionable.",
    avatar: "SC",
  },
  {
    name: "Marcus Johnson",
    role: "High School Debater",
    quote: "Finally, quality coaching accessible to everyone. Vocius helped me win my first tournament!",
    avatar: "MJ",
  },
  {
    name: "Dr. Emily Rodriguez",
    role: "Debate Coach @ Harvard",
    quote: "I use Vocius to supplement my coaching. The analysis depth rivals human expertise.",
    avatar: "ER",
  },
  {
    name: "Alex Kim",
    role: "Policy Debater",
    quote: "The speech delivery feedback is spot-on. My speaking pace and clarity improved dramatically.",
    avatar: "AK",
  },
  {
    name: "Jessica Thompson",
    role: "Parliamentary Debater",
    quote: "Vocius democratizes debate coaching. Every student deserves this level of feedback.",
    avatar: "JT",
  },
  {
    name: "David Park",
    role: "Debate Team Captain",
    quote: "Our entire team uses Vocius. The consistency in coaching quality is unmatched.",
    avatar: "DP",
  },
]

export function Navbar() {
  const pathname = usePathname()
  const [showTestimonials, setShowTestimonials] = useState(false)
  const [showCompanyDropdown, setShowCompanyDropdown] = useState(false)

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between pl-6">
        <div className="flex items-center gap-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-vocius-orange shadow-sm">
              <svg className="h-4 w-4 text-white" fill="currentColor" viewBox="0 0 24 24">
                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z" />
              </svg>
            </div>
            <span className="font-sans text-xl font-bold text-vocius-text">Vocius</span>
          </Link>

          <div className="hidden md:flex items-center gap-6">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.locked ? "#" : item.href}
                className={cn(
                  "text-sm font-medium transition-all duration-300 flex items-center gap-1 px-3 py-2 rounded-lg relative group",
                  item.locked
                    ? "text-muted-foreground cursor-not-allowed"
                    : "hover:text-vocius-orange hover:shadow-lg hover:shadow-vocius-orange/20",
                  pathname === item.href ? "text-vocius-orange" : "text-muted-foreground",
                )}
                onClick={item.locked ? (e) => e.preventDefault() : undefined}
              >
                {!item.locked && (
                  <div className="absolute inset-0 rounded-lg bg-vocius-orange/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                )}
                <span className="relative z-10">{item.name}</span>
                {item.locked && <Lock className="h-3 w-3 relative z-10" />}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setShowTestimonials(true)}
            className="hidden md:flex hover:text-vocius-orange hover:bg-vocius-orange/10 transition-all duration-300 relative group"
          >
            <div className="absolute inset-0 rounded-lg bg-vocius-orange/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
            <Heart className="h-5 w-5 relative z-10" />
            <span className="sr-only">Wall of Love</span>
          </Button>

          <div
            className="relative hidden md:block"
            onMouseEnter={() => setShowCompanyDropdown(true)}
            onMouseLeave={() => setShowCompanyDropdown(false)}
          >
            <Button
              variant="ghost"
              className="flex items-center gap-1 hover:text-vocius-orange hover:bg-vocius-orange/10 transition-all duration-300 relative group px-3 py-2 rounded-lg"
            >
              <div className="absolute inset-0 rounded-lg bg-vocius-orange/10 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <span className="relative z-10">Company</span>
              <ChevronDown className="h-4 w-4 relative z-10" />
            </Button>

            {showCompanyDropdown && (
              <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-50">
                <Link
                  href="/mission-values"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-vocius-orange/10 hover:text-vocius-orange transition-colors"
                >
                  Mission & Values
                </Link>
                <Link
                  href="/leadership"
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-vocius-orange/10 hover:text-vocius-orange transition-colors"
                >
                  Leadership
                </Link>
              </div>
            )}
          </div>

          <Sheet>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="ghost" size="icon">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[400px]">
              <nav className="flex flex-col gap-4">
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    href={item.locked ? "#" : item.href}
                    className={cn(
                      "text-sm font-medium transition-colors flex items-center gap-2 p-2 rounded-md",
                      item.locked
                        ? "text-muted-foreground cursor-not-allowed"
                        : "hover:text-vocius-orange hover:bg-accent",
                      pathname === item.href ? "text-vocius-orange bg-accent" : "text-muted-foreground",
                    )}
                    onClick={item.locked ? (e) => e.preventDefault() : undefined}
                  >
                    {item.name}
                    {item.locked && <Lock className="h-3 w-3" />}
                  </Link>
                ))}
                <Button
                  variant="ghost"
                  onClick={() => setShowTestimonials(true)}
                  className="justify-start p-2 h-auto font-medium text-sm"
                >
                  <Heart className="h-4 w-4 mr-2" />
                  Wall of Love
                </Button>
                <Link href="/mission-values" className="text-sm font-medium p-2 hover:text-vocius-orange">
                  Mission & Values
                </Link>
                <Link href="/leadership" className="text-sm font-medium p-2 hover:text-vocius-orange">
                  Leadership
                </Link>
              </nav>
            </SheetContent>
          </Sheet>

          <Button
            asChild
            variant="outline"
            className="border-2 border-vocius-text/20 text-vocius-text hover:border-vocius-orange hover:text-vocius-orange hover:bg-vocius-orange/5 transition-all duration-300 font-medium bg-transparent"
          >
            <Link href="/login">Login</Link>
          </Button>
        </div>
      </div>

      <Dialog open={showTestimonials} onOpenChange={setShowTestimonials}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-center text-2xl font-bold text-vocius-text mb-4">
              What Our Users Are Saying
            </DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-gray-50 p-4 rounded-lg border hover:shadow-md transition-shadow">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 bg-vocius-orange rounded-full flex items-center justify-center text-white font-medium text-sm">
                    {testimonial.avatar}
                  </div>
                  <div>
                    <div className="font-medium text-sm">{testimonial.name}</div>
                    <div className="text-xs text-muted-foreground">{testimonial.role}</div>
                  </div>
                </div>
                <p className="text-sm text-gray-700 leading-relaxed">"{testimonial.quote}"</p>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </nav>
  )
}
