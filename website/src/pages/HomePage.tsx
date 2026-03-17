import HeroSection from '../components/sections/HeroSection'
import ProblemSection from '../components/sections/ProblemSection'
import BenefitsSection from '../components/sections/BenefitsSection'
import ScreenshotSection from '../components/sections/ScreenshotSection'
import HowItWorksSection from '../components/sections/HowItWorksSection'
import TrustSection from '../components/sections/TrustSection'
import FAQSection from '../components/sections/FAQSection'
import DownloadCTA from '../components/sections/DownloadCTA'

export default function HomePage() {
  return (
    <>
      <HeroSection />
      <ProblemSection />
      <BenefitsSection />
      <ScreenshotSection />
      <HowItWorksSection />
      <TrustSection />
      <FAQSection limit={5} />
      <DownloadCTA />
    </>
  )
}
