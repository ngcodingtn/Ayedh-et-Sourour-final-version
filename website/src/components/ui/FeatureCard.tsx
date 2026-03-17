import type { LucideIcon } from 'lucide-react'

interface FeatureCardProps {
  icon: LucideIcon
  title: string
  description: string
  details?: string[]
}

export default function FeatureCard({
  icon: Icon,
  title,
  description,
  details,
}: FeatureCardProps) {
  return (
    <div className="group relative rounded-2xl border border-slate-200 bg-white p-6 shadow-sm transition-all duration-300 hover:shadow-lg hover:border-brand-200 hover:-translate-y-1">
      <div className="mb-4 inline-flex rounded-xl bg-brand-50 p-3 text-brand-600 transition-colors group-hover:bg-brand-600 group-hover:text-white">
        <Icon className="h-6 w-6" />
      </div>
      <h3 className="mb-2 text-lg font-bold text-slate-900">{title}</h3>
      <p className="text-sm leading-relaxed text-slate-600">{description}</p>
      {details && details.length > 0 && (
        <ul className="mt-4 space-y-1.5">
          {details.map((d) => (
            <li key={d} className="flex items-start gap-2 text-sm text-slate-500">
              <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-brand-400" />
              {d}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
