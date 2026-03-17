import SectionTitle from '../ui/SectionTitle'
import ScreenshotCard from '../ui/ScreenshotCard'
import { screenshots } from '../../data/steps'

export default function ScreenshotSection() {
  return (
    <section className="bg-slate-100/60 py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          title="Voir l'application en action"
          subtitle="Une interface en français, ergonomique, pensée pour réduire le temps de saisie et maximiser la lisibilité des résultats."
        />

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {screenshots.map((s) => (
            <ScreenshotCard key={s.id} {...s} />
          ))}
        </div>
      </div>
    </section>
  )
}
