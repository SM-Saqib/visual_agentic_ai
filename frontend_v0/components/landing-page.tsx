import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight } from "lucide-react"

export default function LandingPage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-[#36393f] text-white p-4">
      <div className="w-full max-w-4xl mx-auto flex flex-col items-center text-center">
        {/* Logo */}
        <div className="mb-8 animate-fade-in">
          <div className="h-32 w-32 bg-[#7289da] rounded-full flex items-center justify-center shadow-lg mb-4">
            <span className="text-4xl font-bold">AI</span>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-2">AI Assistant</h1>
          <p className="text-lg text-gray-300 max-w-md mx-auto">
            Your intelligent companion for conversations and image generation
          </p>
        </div>

        {/* Talk Button */}
        <Link href="/chat" className="mb-12">
          <Button
            size="lg"
            className="bg-[#7289da] hover:bg-[#5865f2] text-white px-8 py-6 text-xl rounded-full transition-all duration-300 shadow-lg hover:shadow-xl flex items-center gap-2"
          >
            Talk
            <ArrowRight className="ml-1" />
          </Button>
        </Link>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full mt-8">
          <FeatureCard
            title="Chat Anytime"
            description="Engage in natural conversations with our AI assistant whenever you need help or company."
            icon="💬"
          />
          <FeatureCard
            title="Generate Images"
            description="Request custom images and watch as our AI creates stunning visuals based on your descriptions."
            icon="🖼️"
          />
          <FeatureCard
            title="Save History"
            description="All your conversations are saved, making it easy to reference past discussions and images."
            icon="📚"
          />
        </div>
      </div>

      {/* Footer */}
      <footer className="mt-auto pt-12 pb-6 text-center text-gray-400 text-sm">
        <p>© 2023 AI Assistant. All rights reserved.</p>
      </footer>
    </div>
  )
}

function FeatureCard({ title, description, icon }: { title: string; description: string; icon: string }) {
  return (
    <div className="bg-[#2f3136] p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow duration-300 border border-[#202225]">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-300">{description}</p>
    </div>
  )
}
