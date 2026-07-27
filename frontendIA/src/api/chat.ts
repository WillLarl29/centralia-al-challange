export type ChatRole = 'user' | 'assistant'

export interface ChatHistoryItem {
  role: ChatRole
  content: string
}

export interface SourceItem {
  id: string
  source: string
  score: number | null
  text: string
}

export interface ChatResponse {
  answer: string
  sources: SourceItem[]
  used_fallback: boolean
}

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export async function sendChatMessage(
  message: string,
  history: ChatHistoryItem[],
): Promise<ChatResponse> {
  const response = await fetch(`${API_URL}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })

  if (!response.ok) {
    throw new Error(`CentralIA respondió con error ${response.status}`)
  }

  return (await response.json()) as ChatResponse
}
