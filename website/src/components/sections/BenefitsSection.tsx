import SectionTitle from '../ui/SectionTitle'
import FeatureCard from '../ui/FeatureCard'
import CTAButton from '../ui/CTAButton'
import { benefits } from '../../data/features'
import { Download } from 'lucide-react'

export default function BenefitsSection() {
  return (
    <section className="py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          title="Conçu pour un dimensionnement fluide et sans erreur"
          subtitle="Tout ce dont vous avez besoin pour justifier vos poutres, réuni dans une interface claire et structurée."
        />

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {benefits.map((b) => (
            <FeatureCard key={b.title} {...b} />
          ))}
        </div>

        <div className="mt-14 text-center">
          <CTAButton to="/telecharger" size="lg">
            <Download className="h-5 w-5" />
            Télécharger l'application
          </CTAButton>
        </div>
      </div>
    </section>
  )
}
