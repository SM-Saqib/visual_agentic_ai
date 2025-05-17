"use client"

import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { formatDistanceToNow } from "date-fns"

interface ChatHistoryItem {
  id: string
  name: string
  lastMessage: string
  timestamp: string
}

interface ChatSidebarProps {
  isOpen: boolean
  onClose: () => void
  chatHistory: ChatHistoryItem[]
}

export default function ChatSidebar({ isOpen, onClose, chatHistory }: ChatSidebarProps) {
  return (
    <div
      className={`fixed inset-y-0 left-0 z-50 w-80 bg-[#2f3136] transform transition-transform duration-300 ease-in-out ${
        isOpen ? "translate-x-0" : "-translate-x-full"
      } md:relative md:translate-x-0 ${isOpen ? "md:block" : "md:hidden"}`}
    >
      <div className="flex items-center justify-between p-4 border-b border-[#202225]">
        <div className="flex items-center">
          <div className="h-10 w-10 rounded-full bg-[#7289da] flex items-center justify-center mr-3">
            <span className="font-bold text-white">AI</span>
          </div>
          <h2 className="text-xl font-bold">Chat History</h2>
        </div>
        <Button
          variant="outline"
          size="icon"
          onClick={onClose}
          className="md:hidden text-gray-200 hover:text-white hover:bg-[#40444b]"
        >
          <X size={24} />
        </Button>
      </div>

      <div className="overflow-y-auto h-[calc(100%-64px)]">
        {chatHistory.map((chat) => (
          <div
            key={chat.id}
            className="p-4 border-b border-[#40444b] hover:bg-[#40444b] cursor-pointer transition-colors"
          >
            <div className="flex justify-between items-start">
              <h3 className="font-medium text-white">{chat.name}</h3>
              <span className="text-xs text-gray-400">
                {formatDistanceToNow(new Date(chat.timestamp), { addSuffix: true })}
              </span>
            </div>
            <p className="text-sm text-gray-300 truncate mt-1">{chat.lastMessage}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
