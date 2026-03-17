import PageHeader from '../components/ui/PageHeader'
import StepCard from '../components/ui/StepCard'
import DownloadCTA from '../components/sections/DownloadCTA'
import { workflowStepsDetailed } from '../data/steps'

export default function HowItWorksPage() {
  return (
    <>
      <PageHeader
        title="Comment ça marche"
        subtitle="Un parcours clair, de la saisie des données à l'exploitation des résultats, en 7 étapes logiques."
      />

      <section className="py-16">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <div className="space-y-0">
            {workflowStepsDetailed.map((step, i) => (
              <StepCard
                key={step.number}
                {...step}
                isLast={i === workflowStepsDetailed.length - 1}
              />
            ))}
          </div>
        </div>
      </section>

      <section className="bg-slate-100/60 py-16">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-slate-900">
            Un workflow pensé pour les poutres en béton armé
          </h2>
          <p className="mt-4 text-slate-600 leading-relaxed">
            Contrairement aux tableurs éparpillés, FlexiBeam relie chaque étape
            du calcul dans un parcours logique et cohérent. Les charges
            alimentent automatiquement les sollicitations, qui alimentent la
            flexion, la fissuration et l'effort tranchant. Modifiez un paramètre
            et tous les résultats se mettent à jour.
          </p>
        </div>
      </section>

      <DownloadCTA />
    </>
  )
}
