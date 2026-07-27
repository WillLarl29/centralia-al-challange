import type { SourceItem } from '../api/chat'

interface Props {
  sources: SourceItem[]
}

export function SourceCitation({ sources }: Props) {
  if (sources.length === 0) return null

  return (
    <details className="mt-2 rounded-lg border border-slate-700/60 bg-slate-900/60 px-3 py-2 text-sm">
      <summary className="cursor-pointer select-none text-slate-400 hover:text-slate-200">
        Fuentes citadas ({sources.length})
      </summary>
      <ul className="mt-2 space-y-2">
        {sources.map((source) => (
          <li key={source.id} className="border-l-2 border-emerald-500/60 pl-2">
            <p className="font-medium text-emerald-400">{source.source}</p>
            <p className="text-slate-400">{source.text}</p>
          </li>
        ))}
      </ul>
    </details>
  )
}
