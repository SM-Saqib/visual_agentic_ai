import { formatDistanceToNow } from "date-fns"
import Image from "next/image"

interface Message {
  id: string
  content: string
  sender: "user" | "ai"
  timestamp: string
  image?: string
}

interface ChatMessageProps {
  message: Message
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.sender === "user"

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-lg p-3 ${isUser ? "bg-[#7289da] text-white" : "bg-[#40444b] text-gray-100"}`}
      >
        <div className="flex items-center mb-1">
          <div
            className={`h-6 w-6 rounded-full ${isUser ? "bg-blue-700" : "bg-[#5865f2]"} flex items-center justify-center mr-2`}
          >
            <span className="text-xs font-bold">{isUser ? "You" : "AI"}</span>
          </div>
          <span className="text-xs opacity-70">
            {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
          </span>
        </div>

        <p className="mb-2">{message.content}</p>

        {message.image && (
          <div className="relative w-full rounded-md overflow-hidden mt-2">
            <Image
              src={message.image || "/placeholder.svg"}
              alt="AI generated image"
              width={800}
              height={600}
              className="w-full h-auto object-cover rounded-md"
            />
          </div>
        )}
      </div>
    </div>
  )
}
