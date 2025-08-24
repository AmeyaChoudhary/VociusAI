"use client"

import { motion } from "framer-motion"
import Image from "next/image"

export default function MissionValuesPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-orange-50/30 to-indigo-50/20">
      {/* Hero Section */}
      <section className="relative py-20 overflow-hidden">
        <div className="absolute inset-0">
          <motion.div
            className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-orange-200/40 to-orange-300/30 rounded-full blur-3xl"
            animate={{
              x: [0, 100, 0],
              y: [0, -50, 0],
            }}
            transition={{
              duration: 20,
              repeat: Number.POSITIVE_INFINITY,
              ease: "easeInOut",
            }}
          />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto px-4 text-center">
          <motion.div initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8 }}>
            <h1 className="font-sans text-4xl md:text-6xl font-bold text-vocius-text mb-6">
              <span className="text-vocius-orange">No Coach?</span> No Problem.
            </h1>
            <p className="text-xl md:text-2xl text-vocius-text/80 font-light">
              Vocius brings championship coaching to every debater.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Founder Section */}
      <section className="py-16 bg-white/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="relative"
            >
              <div className="relative w-80 h-80 mx-auto rounded-2xl overflow-hidden shadow-2xl">
                <Image
                  src="https://hebbkx1anhila5yf.public.blob.vercel-storage.com/Screenshot%202025-08-21%20at%206.49.20%E2%80%AFPM.png-yMNbDWZdgJ8nApc1koY8dmZ0kG1mj8.jpeg"
                  alt="Ameya Choudhary, Founder & CEO"
                  fill
                  className="object-cover"
                />
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              className="space-y-6"
            >
              <blockquote className="text-lg md:text-xl text-vocius-text/90 leading-relaxed italic">
                "I've been to a lot of tournaments and noticed teams with big coaching staffs always have the upper
                hand. Students from smaller schools work just as hard but don't get the same feedback. I built Vocius so
                any debater can upload a round and get the coaching help they deserve."
              </blockquote>
              <div className="border-l-4 border-vocius-orange pl-4">
                <p className="font-semibold text-vocius-text">Ameya Choudhary</p>
                <p className="text-vocius-orange font-medium">Founder & CEO @ Vocius</p>
                <p className="text-vocius-text/70">Student at The Harker School</p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Mission Section */}
      <section className="py-16 bg-gradient-to-r from-slate-50 to-orange-50/30">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="space-y-8"
          >
            <h2 className="font-sans text-3xl md:text-4xl font-bold text-vocius-text">
              Our <span className="text-vocius-orange">Mission</span>
            </h2>
            <p className="text-lg md:text-xl text-vocius-text/80 leading-relaxed">
              Only one in eight U.S. high schools fields an official debate team, and the numbers plunge in high-poverty
              or rural districts. Vocius exists to erase that resource gap—bringing championship-level coaching to the
              23,000+ campuses and hundreds of thousands of students that traditional programs leave behind.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Values Section */}
      <section className="py-16 bg-white/50">
        <div className="max-w-6xl mx-auto px-4">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="font-sans text-3xl md:text-4xl font-bold text-center text-vocius-text mb-12"
          >
            Our <span className="text-vocius-orange">Values</span>
          </motion.h2>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                title: "Accessibility",
                description:
                  "Every student deserves access to quality debate coaching, regardless of their school's resources.",
              },
              {
                title: "Excellence",
                description: "We provide championship-level feedback that helps debaters reach their full potential.",
              },
              {
                title: "Innovation",
                description: "Using cutting-edge AI to democratize debate education and level the playing field.",
              },
            ].map((value, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: index * 0.1 }}
                className="bg-white/80 backdrop-blur-sm rounded-xl p-6 shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <h3 className="font-sans text-xl font-bold text-vocius-orange mb-4">{value.title}</h3>
                <p className="text-vocius-text/80">{value.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
