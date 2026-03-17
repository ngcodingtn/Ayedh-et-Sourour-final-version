export interface Step {
  number: number
  title: string
  description: string
}

export const workflowSteps: Step[] = [
  {
    number: 1,
    title: 'Définir la poutre',
    description:
      'Choisissez le type de poutre (simple ou avec consoles), saisissez la portée, la section et les positions des appuis.',
  },
  {
    number: 2,
    title: 'Renseigner les matériaux',
    description:
      'Définissez la classe du béton (fck), la nuance de l\'acier (fyk), l\'enrobage et les coefficients de sécurité.',
  },
  {
    number: 3,
    title: 'Ajouter les charges',
    description:
      'Saisissez les charges permanentes et variables, réparties ou concentrées. L\'application génère les combinaisons ELU et ELS.',
  },
  {
    number: 4,
    title: 'Calculer les sollicitations',
    description:
      'Obtenez les réactions d\'appui, les diagrammes V(x) et M(x), et les valeurs exactes au point de votre choix.',
  },
  {
    number: 5,
    title: 'Dimensionner et vérifier',
    description:
      'Calculez les armatures longitudinales, vérifiez la flexion, la fissuration et l\'effort tranchant en une seule interface.',
  },
  {
    number: 6,
    title: 'Visualiser et exporter',
    description:
      'Visualisez la poutre en 2D et 3D, lisez les valeurs des diagrammes, et exportez vos résultats.',
  },
]

export const workflowStepsDetailed: Step[] = [
  {
    number: 1,
    title: 'Définir la géométrie de la poutre',
    description:
      'Choisissez entre une poutre simple sur deux appuis ou une poutre avec consoles. Renseignez la portée totale, les positions des appuis, ainsi que la forme de la section (rectangulaire ou en T) avec ses dimensions : largeur, hauteur, table de compression.',
  },
  {
    number: 2,
    title: 'Entrer les matériaux',
    description:
      'Définissez la classe de résistance du béton (fck en MPa), la nuance de l\'acier (fyk en MPa), l\'enrobage nominal et les coefficients partiels de sécurité γc et γs. Ces données conditionnent tous les calculs qui suivent.',
  },
  {
    number: 3,
    title: 'Ajouter les charges',
    description:
      'Saisissez les charges permanentes (G) et variables (Q) en réparti (kN/m) ou en concentré (kN à une position donnée). L\'application gère les combinaisons : ELU, ELS caractéristique, fréquente et quasi-permanente.',
  },
  {
    number: 4,
    title: 'Choisir la combinaison et le point de calcul',
    description:
      'Sélectionnez la combinaison de charges souhaitée et positionnez le curseur de lecture sur la poutre. L\'application calcule RA, RB, V(x), M(x) et identifie les extrema automatiquement.',
  },
  {
    number: 5,
    title: 'Obtenir les efforts et vérifications',
    description:
      'Les moments et efforts tranchants alimentent directement les modules de flexion, de fissuration et d\'effort tranchant. Dimensionnez les aciers, vérifiez les contraintes et validez les espacements — tout est chaîné.',
  },
  {
    number: 6,
    title: 'Visualiser les résultats',
    description:
      'Consultez les schémas 2D de la poutre avec ses charges et appuis, les diagrammes V(x) et M(x), et la vue 3D de la structure. Un marqueur interactif vous permet de lire les valeurs en tout point.',
  },
  {
    number: 7,
    title: 'Exporter et documenter',
    description:
      'Générez un aperçu de rapport complet incluant les résultats de toutes les vérifications, exportez les vues en image, et sauvegardez votre projet au format JSON pour le reprendre plus tard.',
  },
]

export const screenshots = [
  {
    id: 'main',
    title: 'Interface principale',
    description: 'Vue d\'ensemble de l\'application avec la saisie des données.',
    gradient: 'from-brand-800 to-brand-600',
    label: 'Données',
  },
  {
    id: 'elu',
    title: 'Calcul ELU',
    description: 'Résultats du dimensionnement en flexion simple.',
    gradient: 'from-blue-700 to-blue-500',
    label: 'Flexion',
  },
  {
    id: 'fissuration',
    title: 'Module fissuration',
    description: 'Vérification de la fissuration et contraintes ELS.',
    gradient: 'from-emerald-700 to-emerald-500',
    label: 'ELS',
  },
  {
    id: 'sollicitations',
    title: 'Sollicitations',
    description: 'Diagrammes des efforts tranchants et moments fléchissants.',
    gradient: 'from-violet-700 to-violet-500',
    label: 'V(x) & M(x)',
  },
  {
    id: 'ferraillage',
    title: 'Éditeur de ferraillage',
    description: 'Gestion des lits d\'armatures et vérifications constructives.',
    gradient: 'from-amber-700 to-amber-500',
    label: 'Armatures',
  },
  {
    id: 'tranchant',
    title: 'Effort tranchant',
    description: 'Vérification de l\'effort tranchant et étriers.',
    gradient: 'from-rose-700 to-rose-500',
    label: 'VRd',
  },
  {
    id: 'vue2d',
    title: 'Vue 2D',
    description: 'Schéma de la poutre avec cotations et charges.',
    gradient: 'from-cyan-700 to-cyan-500',
    label: '2D',
  },
  {
    id: 'vue3d',
    title: 'Vue 3D',
    description: 'Visualisation 3D interactive de la structure.',
    gradient: 'from-indigo-700 to-indigo-500',
    label: '3D',
  },
]
