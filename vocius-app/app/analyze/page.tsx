import { AnalyzeForm } from "@/components/analyze-form"

export default function AnalyzePage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="font-serif text-3xl font-bold text-center mb-2">Analyze Your Speech</h1>
        <p className="text-muted-foreground text-center mb-8">
          Upload your debate recording and get AI-powered feedback
        </p>
        <AnalyzeForm />
      </div>
    </div>
  )
}
