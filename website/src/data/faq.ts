export interface FAQItem {
  question: string
  answer: string
}

export const faqItems: FAQItem[] = [
  {
    question: 'À quoi sert FlexiBeam ?',
    answer:
      'FlexiBeam est une application de bureau pour le dimensionnement et la vérification des poutres en béton armé. Elle couvre la flexion simple, les sollicitations, l\'effort tranchant, la fissuration, le ferraillage et la visualisation 2D/3D — le tout dans une seule interface.',
  },
  {
    question: 'L\'application fonctionne-t-elle hors ligne ?',
    answer:
      'Oui. Une fois téléchargée, FlexiBeam fonctionne à 100 % hors ligne. Aucune connexion internet n\'est nécessaire et aucune donnée n\'est envoyée vers un serveur.',
  },
  {
    question: 'Existe-t-il une version en ligne ?',
    answer:
      'Non. FlexiBeam est conçu comme un logiciel de bureau (Desktop) pour Windows, ce qui garantit des calculs instantanés et une utilisation fluide sans dépendance réseau.',
  },
  {
    question: 'L\'application est-elle adaptée aux étudiants ?',
    answer:
      'Absolument. L\'interface est visuelle et pédagogique. Elle suit rigoureusement les étapes de conception de l\'Eurocode 2, ce qui permet de comprendre la démarche étape par étape.',
  },
  {
    question: 'Peut-on calculer les moments et efforts tranchants en tout point de la poutre ?',
    answer:
      'Oui. Le module sollicitations permet de calculer V(x) et M(x) en tout point. Vous pouvez positionner un marqueur sur la poutre et lire les valeurs exactes à cet endroit.',
  },
  {
    question: 'La vérification de fissuration est-elle intégrée ?',
    answer:
      'Oui. Le module ELS calcule le moment de fissuration, détecte si la section est fissurée, vérifie les contraintes en service (σ_c et σ_s) et effectue le contrôle simplifié de fissuration selon l\'EC2 §7.3.',
  },
  {
    question: 'L\'application gère-t-elle les sections rectangulaires et en T ?',
    answer:
      'Oui. Vous pouvez basculer entre section rectangulaire et section en T. Le mode automatique détermine le type optimal en fonction de vos données.',
  },
  {
    question: 'Comment télécharger l\'application ?',
    answer:
      'Rendez-vous sur la page Téléchargement, cliquez sur le bouton « Télécharger l\'application » pour obtenir le fichier exécutable. Lancez-le directement — aucune installation complexe n\'est requise.',
  },
  {
    question: 'Que faire si Windows affiche un message de sécurité au lancement ?',
    answer:
      'Windows affiche cet écran pour les applications non publiées sur le Store officiel. Cliquez sur « Informations complémentaires » puis sur « Exécuter quand même ». L\'application est sûre et ne contient aucun logiciel malveillant.',
  },
  {
    question: 'L\'application est-elle gratuite ?',
    answer:
      'Oui. FlexiBeam est disponible en téléchargement gratuit. Aucun abonnement ni licence payante n\'est requis.',
  },
]
