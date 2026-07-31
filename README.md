# Flower Predictor - Classification de fleurs par Deep Learning

Application web de reconnaissance d'images de fleurs basee sur un reseau de neurones convolutif. L'utilisateur televerse une image et le modele predit l'espece parmi cinq categories. L'application propose egalement des tableaux de bord, un systeme de recommandations et une interface bilingue.

## Fonctionnalites

- Classification d'images via un modele ResNet50 pre-entraine
- Reconnaissance de cinq especes : marguerite, pissenlit, rose, tournesol, tulipe
- Interface bilingue (francais / anglais) grace a l'internationalisation Django
- Systeme de recommandations
- Tableaux de bord (espace enseignant et espace etudiant)
- Classement des etudiants (ranking)
- Assistant conversationnel (chatbot)
- Reporting et statistiques

## Stack technique

- Python / Django
- TensorFlow / Keras
- Modele ResNet50 (transfer learning)
- Pillow, NumPy pour le traitement d'images
- HTML / CSS (templates Django)

## Architecture

- `flower_detector` : application principale (modele ML, vues, recommandations, reporting)
- `flower_detector/ml_model` : chargement du modele et logique de prediction
- `flower_detector/model_files` : fichier du modele entraine (resnet50_flowers_model.h5)
- `flower_predictor` : configuration du projet Django
- `locale` : fichiers de traduction (i18n)

## Installation

```bash
git clone https://github.com/narjessmhibik/projet-PI-2BA.git
cd projet-PI-2BA
python -m venv venv
source venv/bin/activate        # sous Windows : venv\Scripts\activate
pip install django tensorflow pillow numpy
python manage.py migrate
python manage.py runserver
```

## Modele

Le modele `resnet50_flowers_model.h5` (environ 46 Mo) est inclus dans le depot.
Les classes reconnues sont : daisy, dandelion, rose, sunflower, tulip.

## Auteur

Narjess Mhibik
