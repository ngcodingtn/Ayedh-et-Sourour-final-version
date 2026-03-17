import SectionTitle from '../ui/SectionTitle'
import FAQAccordion from '../ui/FAQAccordion'
import { faqItems } from '../../data/faq'
import CTAButton from '../ui/CTAButton'

interface FAQSectionProps {
  /** Show only first N items (for homepage summary) */
  limit?: number
}

export default function FAQSection({ limit }: FAQSectionProps) {
  const items = limit ? faqItems.slice(0, limit) : faqItems

  return (
    <section className="py-20">
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          title="Questions fréquentes"
          subtitle="Tout ce que vous devez savoir avant de télécharger FlexiBeam."
        />

        <div className="mt-12">
          <FAQAccordion items={items} />
        </div>

        {limit && (
          <div className="mt-8 text-center">
            <CTAButton to="/faq" variant="ghost">
              Voir toutes les questions →
            </CTAButton>
          </div>
        )}
      </div>
    </section>
  )
}
