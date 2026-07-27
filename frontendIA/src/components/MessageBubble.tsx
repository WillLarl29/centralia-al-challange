import type { Message } from '../hooks/useChat'
import { SourceCitation } from './SourceCitation'

interface Props {
  message: Message
}

export function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
        isUser
          ? 'bg-emerald-600 text-white rounded-br-sm'
          : 'bg-slate-800 text-slate-100 rounded-bl-sm'
      }`}
      >
        <p>{message.content}</p>
        {message.usedFallback && (
          <p className="mt-1 text-xs text-amber-400">
            ⚠ Modo local sin LLM generativo (configura OCI Generative AI para respuestas redactadas)
          </p>
        )}
        {!isUser && message.sources && <SourceCitation sources={message.sources} />}
      </div>
    </div>
  )
}
