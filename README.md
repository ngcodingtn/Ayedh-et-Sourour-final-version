# FlexiBeam – Dimensionnement en Flexion Simple EC2

Application de bureau professionnelle pour le **dimensionnement et la vérification en flexion simple** d'une poutre en béton armé selon l'**Eurocode 2**.

## Fonctionnalités

- **Section rectangulaire** et **section en T** (ou mode automatique)
- Calcul ELU complet :
  - Moment réduit, pivot A/B, bras de levier
  - Aciers comprimés si nécessaire
  - Section minimale EC2
- **Vérification du ferraillage** proposé avec d_réel
- **Catalogue complet des armatures** (HA6 à HA40, 1 à 10 barres)
- **Moteur de proposition** de ferraillage automatique
- **Vérifications constructives** (enrobage, espacement, largeur)
- **Contrôle de fissuration** simplifié (EC2 §7.3)
- **Schéma 2D** (matplotlib) avec cotations
- **Vue 3D** (pyvista) interactive
- **Rapport PDF** complet (reportlab)
- **Sauvegarde / chargement JSON**
- Exemples de validation intégrés
- Interface entièrement en **français**

## Prérequis

- Python 3.11 ou supérieur
- Système d'exploitation : Windows, macOS ou Linux

## Installation

```bash
# Cloner ou extraire le projet
cd beam_design

# Créer un environnement virtuel (recommandé)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# Installer les dépendances
pip install -r requirements.txt
```

## Lancement

```bash
python main.py
```

## Utilisation rapide

1. **Charger un exemple** : cliquez sur « Exemple Rectangulaire » ou « Exemple Section T »
2. **Saisir les données** dans l'onglet « Données »
3. **Calculer** : cliquez sur « CALCULER »
4. **Vérifier le ferraillage** : ajoutez des lits dans l'onglet « Vérification ferraillage »
5. **Proposer des solutions** : cliquez sur « Proposer un ferraillage »
6. **Générer le schéma 2D / 3D** dans les onglets correspondants
7. **Générer le rapport PDF** dans l'onglet « Rapport »

## Architecture du projet

```
beam_design/
├── main.py                          # Point d'entrée
├── requirements.txt                 # Dépendances
├── README.md                        # Ce fichier
├── app/
│   ├── __init__.py
│   ├── config.py                    # Configuration globale
│   ├── constants.py                 # Constantes EC2, catalogue acier
│   ├── models/                      # Modèles de données
│   │   ├── section_models.py        # Géométrie
│   │   ├── material_models.py       # Béton, acier
│   │   ├── load_models.py           # Sollicitations
│   │   ├── reinforcement_models.py  # Ferraillage, environnement
│   │   └── result_models.py         # Résultats de calcul
│   ├── core/                        # Logique de calcul
│   │   ├── units.py                 # Conversions d'unités
│   │   ├── concrete.py              # Calculs béton
│   │   ├── steel.py                 # Calculs acier
│   │   ├── steel_catalog.py         # Catalogue des armatures
│   │   ├── section_geometry.py      # Géométrie de section
│   │   ├── flexion_common.py        # Calculs communs
│   │   ├── flexion_rectangular.py   # Flexion rectangulaire
│   │   ├── flexion_t_beam.py        # Flexion section T
│   │   ├── stress_strain.py         # Contrainte-déformation, pivots
│   │   ├── reinforcement_check.py   # Vérification du ferraillage
│   │   ├── constructive_rules.py    # Règles constructives
│   │   ├── cracking.py              # Fissuration
│   │   ├── serviceability.py        # Calculs ELS
│   │   └── examples.py              # Exemples de validation
│   ├── services/                    # Couche de services
│   │   ├── calculation_service.py   # Orchestration des calculs
│   │   ├── suggestion_service.py    # Proposition de ferraillage
│   │   ├── export_service.py        # Export JSON
│   │   ├── report_service.py        # Génération rapport
│   │   └── persistence_service.py   # Sauvegarde/chargement
│   ├── ui/                          # Interface utilisateur
│   │   ├── styles.py                # Thème et styles
│   │   ├── main_window.py           # Fenêtre principale
│   │   ├── widgets/                 # Widgets réutilisables
│   │   └── dialogs/                 # Boîtes de dialogue
│   ├── visualization/               # Visualisation
│   │   ├── section_plot_2d.py       # Schéma 2D matplotlib
│   │   └── section_view_3d.py       # Vue 3D pyvista
│   ├── reports/                     # Rapports
│   │   └── pdf_report.py            # Génération PDF
│   └── tests/                       # Tests unitaires
│       ├── test_rectangular.py
│       ├── test_t_beam.py
│       ├── test_reinforcement.py
│       ├── test_constructive_rules.py
│       ├── test_cracking.py
│       └── test_integration.py
```

## Unités internes

| Grandeur     | Unité interne | Unité d'affichage |
|-------------|---------------|-------------------|
| Longueurs   | mm            | mm                |
| Contraintes | MPa (N/mm²)   | MPa               |
| Moments     | N·mm          | kN·m              |
| Sections    | mm²           | cm²               |

## Cas de validation

### Exemple rectangulaire
- bw = 350 mm, h = 600 mm, d = 540 mm
- fck = 25 MPa, fyk = 500 MPa
- MEd = 341.4 kN·m
- **Résultat attendu** : As ≈ 16.12 cm², α_u ≈ 0.282

### Exemple section en T
- beff = 2660 mm, bw = 220 mm, hf = 150 mm, h = 850 mm, d = 800 mm
- fck = 25 MPa, MEd = 777 kN·m
- MTu ≈ 4590 kN·m → MEd < MTu → traitement rectangulaire beff
- **Résultat attendu** : As ≈ 22.64 cm²

## Tests

```bash
# Exécuter tous les tests
pytest app/tests/ -v

# Exécuter un fichier de test spécifique
pytest app/tests/test_rectangular.py -v
```

## Licence

Usage académique et professionnel. Projet à but pédagogique et d'ingénierie.

## Auteur

Application développée pour les ingénieurs civils travaillant avec l'Eurocode 2.
