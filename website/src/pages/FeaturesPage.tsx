import { CheckCircle2 } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import DownloadCTA from '../components/sections/DownloadCTA'
import { featuresDetailed } from '../data/features'

export default function FeaturesPage() {
  return (
    <>
      <PageHeader
        title="Fonctionnalités"
        subtitle="Découvrez en détail chaque module de FlexiBeam et comment il simplifie votre travail de dimensionnement."
      />

      <section className="py-16">
        <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div className="space-y-20">
            {featuresDetailed.map((feat, idx) => (
              <div
                key={feat.id}
                className={`flex flex-col gap-10 lg:flex-row lg:items-start ${
                  idx % 2 === 1 ? 'lg:flex-row-reverse' : ''
                }`}
              >
                {/* Image placeholder */}
                <div className="flex-shrink-0 lg:w-96">
                  <div className="flex h-64 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-800 to-brand-600 text-white shadow-lg">
                    <div className="text-center px-6">
                      <div className="text-3xl font-bold opacity-25">
                        {feat.title.split(' ')[0]}
                      </div>
                      <div className="mt-2 rounded-full bg-white/20 px-3 py-1 text-xs">
                        Capture d'écran
                      </div>
                    </div>
                  </div>
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="text-sm font-semibold text-brand-600">
                    {feat.subtitle}
                  </div>
                  <h2 className="mt-1 text-2xl font-bold text-slate-900">
                    {feat.title}
                  </h2>
                  <p className="mt-3 text-slate-600 leading-relaxed">
                    {feat.description}
                  </p>
                  <ul className="mt-5 space-y-2">
                    {feat.items.map((item) => (
                      <li
                        key={item}
                        className="flex items-start gap-2.5 text-sm text-slate-700"
                      >
                        <CheckCircle2 className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" />
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <DownloadCTA />
    </>
  )
}
