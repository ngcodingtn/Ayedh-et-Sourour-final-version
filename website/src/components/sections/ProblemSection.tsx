import { XCircle } from 'lucide-react'
import SectionTitle from '../ui/SectionTitle'

const problems = [
  {
    text: 'Calculs éparpillés',
    detail: 'Passer d\'un tableur à un autre entre la statique, la flexion et les vérifications.',
  },
  {
    text: 'Tableurs fragiles',
    detail: 'Des formules cachées, difficiles à vérifier, à maintenir et à partager.',
  },
  {
    text: 'Manque de lisibilité',
    detail: 'Des résultats noyés dans des cellules sans visualisation claire.',
  },
  {
    text: 'Risque d\'erreurs',
    detail: 'Saisies manuelles, oublis de vérification, conversions d\'unités hasardeuses.',
  },
  {
    text: 'Pertes de temps',
    detail: 'Tout recalculer à chaque modification de charge ou de section.',
  },
]

export default function ProblemSection() {
  return (
    <section className="bg-brand-900 py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          title="Le calcul manuel a ses limites. Les tableurs aussi."
          subtitle="Qu'il s'agisse de projets étudiants ou de vérifications métiers, le dimensionnement béton armé reste souvent une source de dispersion et d'erreurs d'inattention."
          light
        />

        <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {problems.map((p) => (
            <div
              key={p.text}
              className="flex gap-4 rounded-xl border border-white/10 bg-white/5 p-5 backdrop-blur-sm"
            >
              <XCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-400" />
              <div>
                <div className="font-semibold text-white">{p.text}</div>
                <div className="mt-1 text-sm text-slate-400">{p.detail}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
