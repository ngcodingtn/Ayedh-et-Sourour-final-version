import { Target, Lightbulb, GraduationCap, Wrench } from 'lucide-react'
import PageHeader from '../components/ui/PageHeader'
import DownloadCTA from '../components/sections/DownloadCTA'

const values = [
  {
    icon: Target,
    title: 'Objectif clair',
    text: 'Proposer un outil intermédiaire entre le calcul manuel et les logiciels industriels complexes et coûteux, spécifiquement dédié aux poutres en béton armé.',
  },
  {
    icon: Lightbulb,
    title: 'Conception rigoureuse',
    text: 'Chaque module a été conçu en suivant les étapes et formulations de l\'Eurocode 2, avec une attention constante portée à la cohérence entre les données d\'entrée et les résultats.',
  },
  {
    icon: GraduationCap,
    title: 'Valeur pédagogique',
    text: 'L\'interface affiche les étapes intermédiaires du calcul (moment réduit, bras de levier, axe neutre, inertie fissurée) pour permettre à l\'utilisateur de comprendre la démarche, pas seulement le résultat.',
  },
  {
    icon: Wrench,
    title: 'Utilité pratique',
    text: 'Au-delà de la formation, FlexiBeam est un outil fonctionnel : un ingénieur débutant peut s\'en servir pour pré-dimensionner et vérifier une poutre dans un contexte réel.',
  },
]

export default function AboutPage() {
  return (
    <>
      <PageHeader
        title="À propos de FlexiBeam"
        subtitle="Un projet sérieux, construit pour le génie civil."
      />

      <section className="py-16">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="prose prose-lg prose-slate max-w-none">
            <h2 className="text-2xl font-bold text-slate-900">
              Repenser le calcul des structures
            </h2>
            <p className="text-slate-600 leading-relaxed">
              FlexiBeam est né d'un constat simple en ingénierie civile et dans
              l'enseignement : on utilise souvent de multiples tableurs
              disparates pour calculer une seule poutre. Il manquait un outil
              intermédiaire, situé entre l'apprentissage manuel et les logiciels
              industriels complexes — et souvent onéreux.
            </p>
            <p className="text-slate-600 leading-relaxed">
              Ce projet vise à fournir un workflow complet : sans quitter
              l'interface, un utilisateur peut faire varier une charge, observer
              immédiatement l'impact sur le diagramme des moments, et voir
              comment cela affecte le ferraillage ou l'ouverture des fissures.
            </p>
            <p className="text-slate-600 leading-relaxed">
              FlexiBeam a été développé avec rigueur, en respectant les
              principes de dimensionnement de l'Eurocode 2, et en structurant
              le code de manière modulaire et testable. Il représente un travail
              de conception approfondi, mené avec la volonté de produire un
              outil réellement utile — pas un simple exercice académique.
            </p>
          </div>

          <div className="mt-16 grid gap-6 sm:grid-cols-2">
            {values.map((v) => (
              <div
                key={v.title}
                className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <div className="mb-4 inline-flex rounded-xl bg-brand-50 p-3 text-brand-600">
                  <v.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-bold text-slate-900">{v.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-500">
                  {v.text}
                </p>
              </div>
            ))}
          </div>

          <div className="mt-16 rounded-2xl bg-slate-100 p-8 text-center">
            <h2 className="text-xl font-bold text-slate-900">
              Pour qui est FlexiBeam ?
            </h2>
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="rounded-xl bg-white p-5 shadow-sm">
                <div className="text-2xl">🎓</div>
                <h3 className="mt-2 font-bold text-slate-900">Étudiants</h3>
                <p className="mt-1 text-sm text-slate-500">
                  Comprendre les étapes de dimensionnement et réduire les erreurs de calcul.
                </p>
              </div>
              <div className="rounded-xl bg-white p-5 shadow-sm">
                <div className="text-2xl">📚</div>
                <h3 className="mt-2 font-bold text-slate-900">Enseignants</h3>
                <p className="mt-1 text-sm text-slate-500">
                  Disposer d'un outil pédagogique clair et conforme aux normes EC2.
                </p>
              </div>
              <div className="rounded-xl bg-white p-5 shadow-sm">
                <div className="text-2xl">👷</div>
                <h3 className="mt-2 font-bold text-slate-900">Ingénieurs</h3>
                <p className="mt-1 text-sm text-slate-500">
                  Pré-dimensionner et vérifier rapidement des poutres courantes.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <DownloadCTA />
    </>
  )
}
