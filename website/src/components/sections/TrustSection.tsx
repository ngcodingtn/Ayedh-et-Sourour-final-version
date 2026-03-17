import { ShieldCheck, BookOpen, Workflow, Zap } from 'lucide-react'
import SectionTitle from '../ui/SectionTitle'

const trustPoints = [
  {
    icon: ShieldCheck,
    title: 'Calculs conformes EC2',
    text: 'Algorithmes fidèles aux principes de l\'Eurocode 2 pour des résultats fiables et vérifiables.',
  },
  {
    icon: BookOpen,
    title: 'Intérêt pédagogique',
    text: 'Interface visuelle et étapes détaillées permettant de comprendre la démarche de dimensionnement.',
  },
  {
    icon: Workflow,
    title: 'Workflow complet',
    text: 'Des charges aux moments, de la flexion à la fissuration — tout est chaîné dans une logique cohérente.',
  },
  {
    icon: Zap,
    title: 'Résultats instantanés',
    text: 'Calculs en temps réel : modifiez une charge et tous les résultats se mettent à jour immédiatement.',
  },
]

export default function TrustSection() {
  return (
    <section className="bg-slate-100/60 py-20">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <SectionTitle
          title="Un outil sérieux pour des calculs fiables"
          subtitle="FlexiBeam a été pensé et structuré autour d'un algorithme de calcul rigoureux, adapté aux besoins des étudiants, enseignants et jeunes ingénieurs."
        />

        <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {trustPoints.map((tp) => (
            <div
              key={tp.title}
              className="rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-sm"
            >
              <div className="mx-auto mb-4 inline-flex rounded-xl bg-emerald-50 p-3 text-emerald-600">
                <tp.icon className="h-6 w-6" />
              </div>
              <h3 className="font-bold text-slate-900">{tp.title}</h3>
              <p className="mt-2 text-sm text-slate-500">{tp.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
