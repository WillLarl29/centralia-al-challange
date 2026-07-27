import { useCallback, useState } from 'react'
import { sendChatMessage, type ChatHistoryItem, type SourceItem } from '../api/chat'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceItem[]
  usedFallback?: boolean
}

let messageCounter = 0
function nextId(): string {
  messageCounter += 1
  return `msg-${messageCounter}`
}

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || isLoading) return

      const history: ChatHistoryItem[] = messages.map((m) => ({ role: m.role, content: m.content }))
      const userMessage: Message = { id: nextId(), role: 'user', content: trimmed }
      setMessages((prev) => [...prev, userMessage])
      setIsLoading(true)
      setError(null)

      try {
        const response = await sendChatMessage(trimmed, history)
        setMessages((prev) => [
          ...prev,
          {
            id: nextId(),
            role: 'assistant',
            content: response.answer,
            sources: response.sources,
            usedFallback: response.used_fallback,
          },
        ])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error desconocido al contactar a CentralIA')
      } finally {
        setIsLoading(false)
      }
    },
    [messages, isLoading],
  )

  return { messages, isLoading, error, send }
}
