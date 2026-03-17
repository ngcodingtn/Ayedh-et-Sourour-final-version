import { Download, ArrowRight } from 'lucide-react'
import CTAButton from '../ui/CTAButton'

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-slate-50 to-white">
      {/* Decorative grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e2e8f0_1px,transparent_1px),linear-gradient(to_bottom,#e2e8f0_1px,transparent_1px)] bg-[size:4rem_4rem] opacity-40" />

      <div className="relative mx-auto max-w-7xl px-4 py-20 sm:px-6 sm:py-28 lg:px-8 lg:py-36">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          {/* Text */}
          <div>
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-4 py-1.5 text-sm font-medium text-brand-700">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Application de bureau — 100 % hors ligne
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl">
              Calculez et vérifiez vos{' '}
              <span className="bg-gradient-to-r from-brand-600 to-blue-500 bg-clip-text text-transparent">
                poutres en béton armé
              </span>{' '}
              en toute simplicité
            </h1>

            <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-600">
              FlexiBeam réunit la flexion, les sollicitations, l'effort tranchant,
              la fissuration, le ferraillage et la visualisation 2D/3D dans une
              seule application claire et pédagogique.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:gap-4">
              <CTAButton to="/telecharger" size="lg">
                <Download className="h-5 w-5" />
                Télécharger l'application
              </CTAButton>
              <CTAButton to="/fonctionnalites" variant="secondary" size="lg">
                Découvrir les fonctionnalités
                <ArrowRight className="h-5 w-5" />
              </CTAButton>
            </div>

            <div className="mt-8 flex items-center gap-6 text-sm text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Gratuit
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Windows
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Eurocode 2
              </span>
            </div>
          </div>

          {/* Visual mockup */}
          <div className="relative">
            <div className="relative rounded-2xl border border-slate-200 bg-gradient-to-br from-brand-900 to-brand-800 p-2 shadow-2xl shadow-brand-900/20">
              {/* Title bar */}
              <div className="flex items-center gap-2 rounded-t-xl bg-brand-950 px-4 py-2.5">
                <div className="flex gap-1.5">
                  <div className="h-3 w-3 rounded-full bg-red-400/80" />
                  <div className="h-3 w-3 rounded-full bg-amber-400/80" />
                  <div className="h-3 w-3 rounded-full bg-emerald-400/80" />
                </div>
                <span className="ml-3 text-xs text-slate-400">FlexiBeam — Dimensionnement EC2</span>
              </div>
              {/* Screen placeholder */}
              <div className="flex h-72 items-center justify-center rounded-b-xl bg-gradient-to-br from-slate-800 to-slate-900 sm:h-80 lg:h-96">
                <div className="text-center px-8">
                  <div className="text-5xl font-extrabold text-brand-400/20">FlexiBeam</div>
                  <p className="mt-2 text-sm text-slate-500">
                    Remplacez ce bloc par une capture d'écran de l'application
                  </p>
                </div>
              </div>
            </div>
            {/* Floating badge */}
            <div className="absolute -bottom-4 -right-4 rounded-xl bg-white px-4 py-3 shadow-lg border border-slate-100">
              <div className="text-xs font-medium text-slate-500">Modules intégrés</div>
              <div className="text-2xl font-bold text-brand-600">7+</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
