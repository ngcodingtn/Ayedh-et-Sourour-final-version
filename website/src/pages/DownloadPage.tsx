import {
  Download,
  Monitor,
  WifiOff,
  ShieldCheck,
  HardDrive,
  MousePointerClick,
  Info,
  Play,
} from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'

export default function DownloadPage() {
  return (
    <>
      <PageHeader
        title="Télécharger FlexiBeam"
        subtitle="Application de bureau pour Windows — exécutable autonome, sans installation."
      />

      <section className="py-16">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          {/* Download card */}
          <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg">
            <div className="bg-gradient-to-r from-brand-800 to-brand-600 px-8 py-10 text-center text-white">
              <div className="mx-auto mb-4 inline-flex rounded-2xl bg-white/15 p-4">
                <Download className="h-10 w-10" />
              </div>
              <h2 className="text-2xl font-bold">FlexiBeam pour Windows</h2>
              <p className="mt-2 text-brand-200">
                Dimensionnement et vérification des poutres en béton armé
              </p>

              <a
                href="https://github.com/ngcodingtn/Ayedh-et-Sourour-final-version/releases"
                target="_blank"
                rel="noopener noreferrer"
                className="mt-6 inline-flex items-center gap-2 rounded-xl bg-white px-8 py-4 text-lg font-bold text-brand-800 shadow-lg transition-all hover:bg-brand-50 hover:shadow-xl"
              >
                <Download className="h-5 w-5" />
                Télécharger l'application
              </a>
            </div>

            {/* Info grid */}
            <div className="grid divide-y divide-slate-100 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
              <div className="flex items-center gap-3 px-6 py-4">
                <Monitor className="h-5 w-5 text-slate-400" />
                <div>
                  <div className="text-xs text-slate-400">Système</div>
                  <div className="font-semibold text-slate-700">Windows 10+</div>
                </div>
              </div>
              <div className="flex items-center gap-3 px-6 py-4">
                <HardDrive className="h-5 w-5 text-slate-400" />
                <div>
                  <div className="text-xs text-slate-400">Taille</div>
                  <div className="font-semibold text-slate-700">~ 197 Mo</div>
                </div>
              </div>
              <div className="flex items-center gap-3 px-6 py-4">
                <WifiOff className="h-5 w-5 text-slate-400" />
                <div>
                  <div className="text-xs text-slate-400">Réseau</div>
                  <div className="font-semibold text-slate-700">Hors ligne</div>
                </div>
              </div>
            </div>
          </div>

          {/* How to launch */}
          <div className="mt-12">
            <h2 className="text-2xl font-bold text-slate-900">
              Comment lancer l'application
            </h2>
            <div className="mt-6 space-y-4">
              {[
                {
                  icon: Download,
                  step: '1',
                  title: 'Téléchargez le fichier',
                  text: 'Cliquez sur le bouton ci-dessus pour télécharger le fichier exécutable (main.exe).',
                },
                {
                  icon: MousePointerClick,
                  step: '2',
                  title: 'Double-cliquez sur le fichier',
                  text: 'Ouvrez le fichier téléchargé. L\'application se lance directement — aucune installation n\'est nécessaire.',
                },
                {
                  icon: Info,
                  step: '3',
                  title: 'Si Windows affiche un avertissement',
                  text: 'Windows SmartScreen peut s\'afficher pour les applications non signées. Cliquez sur « Informations complémentaires » puis sur « Exécuter quand même ».',
                },
                {
                  icon: Play,
                  step: '4',
                  title: 'Utilisez FlexiBeam',
                  text: 'L\'application s\'ouvre. Vous pouvez commencer à saisir vos données et calculer vos poutres immédiatement.',
                },
              ].map((s) => (
                <div
                  key={s.step}
                  className="flex gap-4 rounded-xl border border-slate-200 bg-white p-5"
                >
                  <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                    <s.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-semibold text-slate-900">
                      <span className="text-brand-600">Étape {s.step}.</span>{' '}
                      {s.title}
                    </div>
                    <p className="mt-1 text-sm text-slate-500">{s.text}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Trust block */}
          <div className="mt-12 rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
            <div className="flex gap-4">
              <ShieldCheck className="h-6 w-6 flex-shrink-0 text-emerald-600" />
              <div>
                <h3 className="font-bold text-emerald-900">
                  Téléchargement sécurisé
                </h3>
                <p className="mt-1 text-sm text-emerald-700">
                  FlexiBeam est un projet open-source hébergé sur GitHub.
                  L'application ne collecte aucune donnée personnelle, ne nécessite
                  aucun compte et fonctionne intégralement hors ligne. Vos
                  fichiers de projet restent sur votre machine.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
