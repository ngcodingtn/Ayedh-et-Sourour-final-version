import SectionTitle from '../ui/SectionTitle'
import StepCard from '../ui/StepCard'
import { workflowSteps } from '../../data/steps'

export default function HowItWorksSection() {
  return (
    <section className="py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          title="De la géométrie aux résultats en 6 étapes"
          subtitle="Un workflow structuré pour ne rien oublier dans votre dimensionnement."
        />

        <div className="mx-auto mt-14 max-w-2xl">
          {workflowSteps.map((step, i) => (
            <StepCard
              key={step.number}
              {...step}
              isLast={i === workflowSteps.length - 1}
            />
          ))}
        </div>
      </div>
    </section>
  )
}
