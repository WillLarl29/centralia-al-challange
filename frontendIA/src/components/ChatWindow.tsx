import { useEffect, useRef, useState } from 'react'
import { useChat } from '../hooks/useChat'
import { MessageBubble } from './MessageBubble'

export function ChatWindow() {
  const { messages, isLoading, error, send } = useChat()
  const [input, setInput] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    const text = input
    setInput('')
    void send(text)
  }

  return (
    <div className="mx-auto flex h-full w-full max-w-3xl flex-col">
      <header className="border-b border-slate-800 px-4 py-4">
        <h1 className="text-xl font-semibold text-white">CentralIA</h1>
        <p className="text-sm text-slate-400">
          Agente de IA corporativo de Mercado Central 24h — RH, Compras, Legal, Operaciones y Atención al Cliente.
        </p>
      </header>

      <div className="flex-1 space-y-4 overflow-y-auto px-4 py-6">
        {messages.length === 0 && (
          <div className="rounded-xl border border-dashed border-slate-700 p-6 text-center text-slate-400">
            Pregúntame algo sobre las políticas internas, RH, compras, atención al cliente o el
            inventario de Mercado Central 24h. Por ejemplo: <br />
            <span className="italic">
              "¿Cuál es el plazo de devolución de productos perecederos?"
            </span>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="rounded-2xl rounded-bl-sm bg-slate-800 px-4 py-3 text-sm text-slate-400">
              CentralIA está escribiendo…
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-500/50 bg-red-950/40 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-slate-800 p-4">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Escribe tu pregunta para CentralIA…"
            className="flex-1 rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-slate-100 outline-none focus:border-emerald-500"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="rounded-xl bg-emerald-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Enviar
          </button>
        </div>
      </form>
    </div>
  )
}
