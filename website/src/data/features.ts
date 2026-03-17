import {
  Ruler,
  Layers,
  ShieldCheck,
  BarChart3,
  Scissors,
  Box,
  WifiOff,
  FileText,
  type LucideIcon,
} from 'lucide-react'

export interface Feature {
  icon: LucideIcon
  title: string
  description: string
  details: string[]
}

export const benefits: Feature[] = [
  {
    icon: Ruler,
    title: 'Flexion simple',
    description:
      'Dimensionnez vos sections rectangulaires ou en T et obtenez instantanément les sections d\'acier nécessaires.',
    details: [
      'Sections rectangulaires et en T',
      'Moment réduit et bras de levier',
      'Aciers comprimés si nécessaire',
      'Section minimale EC2',
    ],
  },
  {
    icon: Layers,
    title: 'Ferraillage vérifié',
    description:
      'Gérez précisément vos lits d\'armatures, vérifiez les espacements et les enrobages en un clic.',
    details: [
      'Catalogues HA6 à HA40',
      'Gestion multi-lits',
      'Vérification de l\'enrobage',
      'Propositions automatiques',
    ],
  },
  {
    icon: ShieldCheck,
    title: 'Fissuration & ELS',
    description:
      'Calculez le moment de fissuration et vérifiez les contraintes de service selon l\'Eurocode 2.',
    details: [
      'Moment de fissuration Mcr',
      'Inertie fissurée',
      'Contraintes σ_c et σ_s',
      'Contrôle simplifié de fissuration',
    ],
  },
  {
    icon: BarChart3,
    title: 'Sollicitations complètes',
    description:
      'Saisissez vos charges, l\'application génère les combinaisons et trace V(x) et M(x).',
    details: [
      'Charges G, Q, concentrées',
      'Combinaisons ELU / ELS',
      'Réactions d\'appui',
      'Diagrammes automatiques',
    ],
  },
  {
    icon: Scissors,
    title: 'Effort tranchant',
    description:
      'Vérifiez VRd,c, VRd,max et calculez le ferraillage transversal requis.',
    details: [
      'Résistance béton VRd,c',
      'Résistance bielles VRd,max',
      'Asw/s requis',
      'Espacement des étriers',
    ],
  },
  {
    icon: Box,
    title: 'Visualisation 2D & 3D',
    description:
      'Ne calculez plus à l\'aveugle : visualisez la poutre, les charges et les diagrammes en 2D et 3D.',
    details: [
      'Schéma de la poutre avec charges',
      'Diagrammes V(x) et M(x)',
      'Vue 3D interactive',
      'Marqueur de position x',
    ],
  },
  {
    icon: WifiOff,
    title: '100 % hors ligne',
    description:
      'Aucune connexion internet requise. Vos données restent sur votre machine.',
    details: [
      'Application de bureau autonome',
      'Pas de compte à créer',
      'Pas de données envoyées',
      'Utilisable partout',
    ],
  },
  {
    icon: FileText,
    title: 'Rapports & export',
    description:
      'Exportez vos résultats et générez des rapports de calcul clairs et documentés.',
    details: [
      'Aperçu du rapport complet',
      'Export des vues 2D/3D',
      'Sauvegarde JSON',
      'Documentation de calcul',
    ],
  },
]

export const featuresDetailed = [
  {
    id: 'flexion',
    title: 'Flexion simple & Géométrie',
    subtitle: 'Le cœur du dimensionnement',
    description:
      'Gérez les poutres à section rectangulaire ou en T. Dimensionnez les armatures longitudinales à partir du moment sollicitant, avec prise en charge automatique des aciers comprimés si le moment dépasse la capacité de la section simple.',
    items: [
      'Section rectangulaire complète',
      'Section en T avec table de compression',
      'Détection automatique du type de section optimal',
      'Moment réduit μ, bras de levier z',
      'Pivots A et B, domaine de déformation',
      'Aciers comprimés As\' si nécessaire',
      'Section minimale selon l\'EC2',
    ],
  },
  {
    id: 'ferraillage',
    title: 'Vérification du ferraillage',
    subtitle: 'Précision et conformité',
    description:
      'Disposez vos armatures par lits, choisissez diamètres et nombre de barres, et vérifiez instantanément la conformité avec les règles constructives de l\'Eurocode 2.',
    items: [
      'Catalogue complet HA6 à HA40',
      'Gestion de 1 à 10 barres par lit',
      'Multi-lits avec enrobage réel',
      'Hauteur utile d réelle calculée',
      'Vérification d\'espacement et d\'enrobage',
      'Propositions automatiques de ferraillage',
    ],
  },
  {
    id: 'fissuration',
    title: 'Fissuration & ELS',
    subtitle: 'Maîtriser l\'état de service',
    description:
      'Vérifiez intégralement le comportement en service de votre poutre : moment de fissuration, état fissuré ou non, contraintes limites, et contrôle simplifié de l\'ouverture des fissures.',
    items: [
      'Moment de fissuration Mcr (rect. et T)',
      'Détection automatique section fissurée',
      'Contraintes σ_c et σ_s en service',
      'Limites 0,6·fck et 0,8·fyk',
      'Inertie fissurée et axe neutre',
      'As,min selon EC2 §7.3',
      'Contrôle simplifié par diamètre et espacement',
    ],
  },
  {
    id: 'sollicitations',
    title: 'Sollicitations de la poutre',
    subtitle: 'De la charge aux efforts',
    description:
      'Modélisez votre poutre isostatique, ajoutez des charges réparties et concentrées, et obtenez automatiquement les réactions d\'appui, les diagrammes d\'efforts tranchants et de moments fléchissants.',
    items: [
      'Poutre simple ou avec consoles',
      'Charges permanentes G et variables Q',
      'Charges concentrées positionnées',
      'Combinaisons ELU, ELS caractéristique, fréquente, quasi-permanente',
      'Réactions d\'appui RA et RB',
      'Diagrammes V(x) et M(x) automatiques',
      'Extrema localisés',
    ],
  },
  {
    id: 'effort-tranchant',
    title: 'Effort tranchant',
    subtitle: 'Sécuriser la structure',
    description:
      'Vérifiez la résistance à l\'effort tranchant selon l\'EC2 §6.2 : résistance du béton seul, nécessité d\'armatures transversales, résistance des bielles comprimées, et dimensionnement des étriers.',
    items: [
      'VRd,c — résistance béton seul',
      'VRd,s — résistance des armatures transversales',
      'VRd,max — vérification des bielles comprimées',
      'Asw/s requis et dispositions minimales',
      'Espacement maximal des étriers',
      'Verdict automatique',
    ],
  },
  {
    id: 'visualisation',
    title: 'Visualisation 2D & 3D',
    subtitle: 'Voir pour comprendre',
    description:
      'FlexiBeam intègre un moteur de visualisation qui vous permet de voir votre poutre, ses charges, ses diagrammes et sa section en 2D et en 3D directement dans l\'application.',
    items: [
      'Schéma 2D de la poutre avec charges et appuis',
      'Diagrammes V(x) et M(x) interactifs',
      'Marqueur de position x avec lecture des valeurs',
      'Vue 3D de la structure complète',
      'Section transversale cotée',
      'Export des vues en image',
    ],
  },
  {
    id: 'export',
    title: 'Rapports & export',
    subtitle: 'Documenter vos calculs',
    description:
      'Exportez vos résultats sous forme de rapport complet incluant toutes les vérifications, ou sauvegardez votre projet en JSON pour le reprendre plus tard.',
    items: [
      'Aperçu du rapport de calcul',
      'Résultats ELU, ELS, fissuration, effort tranchant',
      'Sauvegarde et chargement de projets JSON',
      'Export des vues 2D et 3D',
      'Documentation complète des hypothèses',
    ],
  },
]
