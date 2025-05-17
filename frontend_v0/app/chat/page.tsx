"use client"

import React, { useState, useEffect, useRef } from "react"
import ChatHeader from "@/components/chat-header"
import ChatSidebar from "@/components/chat-sidebar"
import ChatInput from "@/components/chat-input"
import ChatMessage from "@/components/chat-message"



// Sample chat history data
const initialMessages = [
  {
    id: "1",
    content: "Hello! I am Felicia, How may I help you?",
    sender: "ai",
    timestamp: new Date(Date.now() - 3600000).toISOString(),
  },
  {
    id: "2",
    content: "Here's a mountain landscape I created for you:",
    sender: "ai",
    timestamp: new Date(Date.now() - 3400000).toISOString(),
    image: "/placeholder.svg?height=600&width=800",
  }
]

// Sample chat history
const chatHistory = [
  {
    id: "1",
    name: "Mountain Landscapes",
    lastMessage: "Here's a snowy mountain landscape",
    timestamp: new Date(Date.now() - 3200000).toISOString(),
  },
  {
    id: "2",
    name: "City Skylines",
    lastMessage: "I've created a futuristic city skyline",
    timestamp: new Date(Date.now() - 86400000).toISOString(),
  },
  {
    id: "3",
    name: "Character Designs",
    lastMessage: "Here's the fantasy character you requested",
    timestamp: new Date(Date.now() - 172800000).toISOString(),
  },
]



export default function ChatPage() {
  const [messages, setMessages] = useState(initialMessages)
  const [inputValue, setInputValue] = useState("")
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const websocketRef = useRef(null)

  const clientId = useRef(`client_${Date.now()}`)
  const conversationId = useRef(`conversation_${Date.now()}`)

  // Connect to WebSocket
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/api/ws") // Use wss:// in production
    websocketRef.current = ws

    ws.onopen = () => {
      console.log("WebSocket connected")

      // Send initial handshake message
      ws.send(
        JSON.stringify({
          client_id: clientId.current,
          conversation_id: conversationId.current,
        })
      )
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.message) {
          const aiMessage = {
            id: Date.now().toString(),
            content: data.message,
            sender: "ai",
            timestamp: new Date().toISOString(),
          }
          setMessages((prev) => [...prev, aiMessage])
        }
      } catch (e) {
        console.error("WebSocket message parse error:", e)
      }
    }

    ws.onerror = (e) => {
      console.error("WebSocket error:", e)
    }

    ws.onclose = () => {
      console.log("WebSocket disconnected")
    }

    return () => {
      ws.close()
    }
  }, [])

  // Send message handler
  const handleSendMessage = () => {
    if (!inputValue.trim()) return

    const userMessage = {
      id: Date.now().toString(),
      content: inputValue,
      sender: "user",
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])

    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(
        JSON.stringify({
          type: "normal_chat",
          client_id: clientId.current,
          message: inputValue,
        })
      )
    } else {
      console.error("WebSocket is not open")
    }

    setInputValue("")
  }

  return (
        <div className="flex h-screen bg-[#36393f] text-white">
          {/* Sidebar */}
          <ChatSidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} chatHistory={chatHistory} />
    
          {/* Main Chat Area */}
          <div className="flex flex-col w-full h-full">
            <ChatHeader
              title="AI Assistant"
              onMenuClick={() => setSidebarOpen((prev) => !prev)}
            />
    
            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <ChatMessage key={message.id} message={message} />
              ))}
            </div>
    
            {/* Chat Input */}
            <ChatInput value={inputValue} onChange={(e) => setInputValue(e.target.value)} onSend={handleSendMessage} />
          </div>
        </div>
      )
    }