interface StepCardProps {
  number: number
  title: string
  description: string
  isLast?: boolean
}

export default function StepCard({ number, title, description, isLast }: StepCardProps) {
  return (
    <div className="relative flex gap-6">
      {/* Connector line */}
      {!isLast && (
        <div className="absolute left-6 top-14 h-full w-0.5 bg-brand-200" />
      )}
      {/* Number badge */}
      <div className="relative z-10 flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-brand-600 text-lg font-bold text-white shadow-lg shadow-brand-600/25">
        {number}
      </div>
      {/* Content */}
      <div className="pb-10">
        <h3 className="text-lg font-bold text-slate-900">{title}</h3>
        <p className="mt-1 text-slate-600 leading-relaxed">{description}</p>
      </div>
    </div>
  )
}
