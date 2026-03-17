import { Download, WifiOff, Monitor } from 'lucide-react'
import CTAButton from '../ui/CTAButton'

export default function DownloadCTA() {
  return (
    <section className="bg-gradient-to-br from-brand-900 via-brand-800 to-brand-900 py-20">
      <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold tracking-tight text-white sm:text-4xl">
          Passez à un dimensionnement plus intelligent
        </h2>
        <p className="mt-4 text-lg text-brand-200">
          Accélérez vos calculs en béton armé sans connexion internet et sans
          installation complexe.
        </p>

        <div className="mt-8">
          <CTAButton to="/telecharger" size="lg" className="bg-white !text-brand-800 hover:bg-brand-50 !shadow-white/20">
            <Download className="h-5 w-5" />
            Télécharger l'application
          </CTAButton>
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-6 text-sm text-brand-300">
          <span className="flex items-center gap-2">
            <Monitor className="h-4 w-4" />
            Windows
          </span>
          <span className="flex items-center gap-2">
            <WifiOff className="h-4 w-4" />
            100 % hors ligne
          </span>
          <span className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Gratuit
          </span>
        </div>
      </div>
    </section>
  )
}
