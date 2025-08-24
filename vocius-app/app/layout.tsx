import type React from "react"
import type { Metadata } from "next"
import { Outfit, Inter } from "next/font/google"
import "./globals.css"
import { Toaster } from "sonner"
import { Navbar } from "@/components/navbar"

const outfit = Outfit({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-outfit",
})

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
})

export const metadata: Metadata = {
  title: "Vocius - AI Debate Judge & Speech Coach",
  description: "Where Voice Meets Victory. Advanced AI-powered debate analysis and speech coaching.",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${outfit.variable} ${inter.variable} antialiased`}>
      <body className="min-h-screen bg-vocius-bg font-sans antialiased text-vocius-text">
        <Navbar />
        <main>{children}</main>
        <Toaster position="top-center" richColors />
      </body>
    </html>
  )
}
