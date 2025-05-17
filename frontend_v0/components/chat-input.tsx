"use client"

import { Send, ImageIcon } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { ChangeEvent, FormEvent, KeyboardEvent } from "react"

interface ChatInputProps {
  value: string
  onChange: (e: ChangeEvent<HTMLTextAreaElement>) => void
  onSend: () => void
}

export default function ChatInput({ value, onChange, onSend }: ChatInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      onSend()
    }
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    onSend()
  }

  return (
    <div className="p-4 bg-[#40444b] border-t border-[#202225]">
      <form onSubmit={handleSubmit} className="flex items-end gap-2">
        <Button type="button" variant="ghost" size="icon" className="text-gray-300 hover:text-white hover:bg-[#36393f]">
          <ImageIcon size={20} />
        </Button>

        <div className="flex-1 relative">
          <textarea
            value={value}
            onChange={onChange}
            onKeyDown={handleKeyDown}
            placeholder="Message AI Assistant..."
            className="w-full resize-none rounded-md bg-[#36393f] border-none text-white p-3 min-h-[40px] max-h-[120px] focus:outline-none focus:ring-1 focus:ring-[#7289da]"
            rows={1}
          />
        </div>

        <Button
          type="submit"
          variant="ghost"
          size="icon"
          disabled={!value.trim()}
          className={`text-gray-300 hover:text-white hover:bg-[#36393f] ${!value.trim() ? "opacity-50 cursor-not-allowed" : ""}`}
        >
          <Send size={20} />
        </Button>
      </form>
    </div>
  )
}
