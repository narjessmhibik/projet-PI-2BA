from django.core.management.base import BaseCommand
from flower_detector.models import Achievement

class Command(BaseCommand):
    help = 'Créer les achievements par défaut'

    def handle(self, *args, **kwargs):
        achievements = [
            # Débutant
            {
                'name': 'Premier Pas',
                'description': 'Effectuer votre première prédiction',
                'category': 'beginner',
                'icon': '🌱',
                'requirement_type': 'total_predictions',
                'requirement_value': 1,
                'points': 10,
            },
            {
                'name': 'Collectionneur Débutant',
                'description': 'Identifier 10 fleurs',
                'category': 'beginner',
                'icon': '🌼',
                'requirement_type': 'total_predictions',
                'requirement_value': 10,
                'points': 20,
            },
            
            # Explorateur
            {
                'name': 'Explorateur',
                'description': 'Découvrir toutes les 5 espèces de fleurs',
                'category': 'explorer',
                'icon': '🔍',
                'requirement_type': 'flowers_discovered',
                'requirement_value': 5,
                'points': 50,
            },
            {
                'name': 'Aventurier',
                'description': 'Effectuer 50 prédictions',
                'category': 'explorer',
                'icon': '🚀',
                'requirement_type': 'total_predictions',
                'requirement_value': 50,
                'points': 50,
            },
            
            # Expert
            {
                'name': 'Expert Botaniste',
                'description': 'Effectuer 100 prédictions',
                'category': 'expert',
                'icon': '🎓',
                'requirement_type': 'total_predictions',
                'requirement_value': 100,
                'points': 100,
            },
            {
                'name': 'Précision Parfaite',
                'description': 'Atteindre un score de confiance moyen de 90%',
                'category': 'expert',
                'icon': '🎯',
                'requirement_type': 'high_accuracy',
                'requirement_value': 90,
                'points': 75,
            },
            
            # Régularité
            {
                'name': 'Habitué',
                'description': 'Utiliser l\'app 3 jours consécutifs',
                'category': 'streak',
                'icon': '📅',
                'requirement_type': 'streak',
                'requirement_value': 3,
                'points': 30,
            },
            {
                'name': 'Dédié',
                'description': 'Utiliser l\'app 7 jours consécutifs',
                'category': 'streak',
                'icon': '🔥',
                'requirement_type': 'streak',
                'requirement_value': 7,
                'points': 60,
            },
            {
                'name': 'Maître de la Discipline',
                'description': 'Utiliser l\'app 30 jours consécutifs',
                'category': 'streak',
                'icon': '👑',
                'requirement_type': 'streak',
                'requirement_value': 30,
                'points': 150,
            },
        ]
        
        created_count = 0
        for ach_data in achievements:
            achievement, created = Achievement.objects.get_or_create(
                name=ach_data['name'],
                defaults=ach_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Créé: {achievement.icon} {achievement.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 {created_count} achievements créés!')
        )