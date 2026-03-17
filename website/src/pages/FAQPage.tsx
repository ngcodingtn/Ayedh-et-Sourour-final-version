import PageHeader from '../components/ui/PageHeader'
import FAQAccordion from '../components/ui/FAQAccordion'
import DownloadCTA from '../components/sections/DownloadCTA'
import { faqItems } from '../data/faq'

export default function FAQPage() {
  return (
    <>
      <PageHeader
        title="Foire aux questions"
        subtitle="Retrouvez ici les réponses aux questions les plus courantes sur FlexiBeam."
      />

      <section className="py-16">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8">
          <FAQAccordion items={faqItems} />
        </div>
      </section>

      <DownloadCTA />
    </>
  )
}
