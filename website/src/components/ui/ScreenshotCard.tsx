interface ScreenshotCardProps {
  title: string
  description: string
  gradient: string
  label: string
}

export default function ScreenshotCard({
  title,
  description,
  gradient,
  label,
}: ScreenshotCardProps) {
  return (
    <div className="group overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-all duration-300 hover:shadow-lg hover:-translate-y-1">
      {/* Placeholder for screenshot */}
      <div
        className={`relative flex h-48 items-center justify-center bg-gradient-to-br ${gradient}`}
      >
        <div className="text-center text-white">
          <div className="mb-2 text-4xl font-bold opacity-30">{label}</div>
          <div className="rounded-full bg-white/20 px-3 py-1 text-xs font-medium backdrop-blur-sm">
            Capture d'écran
          </div>
        </div>
      </div>
      <div className="p-4">
        <h3 className="font-bold text-slate-900">{title}</h3>
        <p className="mt-1 text-sm text-slate-500">{description}</p>
      </div>
    </div>
  )
}
