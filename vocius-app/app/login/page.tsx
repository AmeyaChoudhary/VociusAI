import { LoginForm } from "@/components/login-form"

export default function LoginPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-md mx-auto">
        <div className="text-center mb-8">
          <h1 className="font-serif text-3xl font-bold mb-2">Welcome Back</h1>
          <p className="text-muted-foreground">Sign in to your Vocius account</p>
        </div>
        <LoginForm />
      </div>
    </div>
  )
}
