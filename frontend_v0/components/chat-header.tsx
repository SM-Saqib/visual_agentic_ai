"use client"

import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ChatHeaderProps {
  title: string
  onMenuClick: () => void
}

export default function ChatHeader({ title, onMenuClick }: ChatHeaderProps) {
  return (
    <header className="flex items-center px-4 py-3 bg-[#2f3136] border-b border-[#202225]">
      <Button
        variant="ghost"
        size="icon"
        onClick={onMenuClick}
        className="mr-2 text-gray-200 hover:text-white hover:bg-[#40444b]"
      >
        <Menu size={24} />
      </Button>
      <div className="flex items-center">
        <div className="h-8 w-8 rounded-full bg-[#7289da] flex items-center justify-center mr-3">
          <span className="font-bold text-white">AI</span>
        </div>
        <h1 className="text-xl font-semibold">{title}</h1>
      </div>
    </header>
  )
}
