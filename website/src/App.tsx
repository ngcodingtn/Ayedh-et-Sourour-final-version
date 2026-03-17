import { Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Footer from './components/layout/Footer'
import HomePage from './pages/HomePage'
import FeaturesPage from './pages/FeaturesPage'
import HowItWorksPage from './pages/HowItWorksPage'
import DownloadPage from './pages/DownloadPage'
import FAQPage from './pages/FAQPage'
import AboutPage from './pages/AboutPage'
import ScrollToTop from './components/ui/ScrollToTop'

export default function App() {
  return (
    <div className="flex min-h-screen flex-col">
      <ScrollToTop />
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/fonctionnalites" element={<FeaturesPage />} />
          <Route path="/comment-ca-marche" element={<HowItWorksPage />} />
          <Route path="/telecharger" element={<DownloadPage />} />
          <Route path="/faq" element={<FAQPage />} />
          <Route path="/a-propos" element={<AboutPage />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
