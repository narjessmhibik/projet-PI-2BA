from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from flower_detector.recommendations import get_smart_recommendations

class Command(BaseCommand):
    help = 'Génère des recommandations pour tous les utilisateurs'

    def handle(self, *args, **kwargs):
        users = User.objects.filter(is_active=True)
        
        for user in users:
            recommendations = get_smart_recommendations(user)
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ {recommendations.count()} recommandations générées pour {user.username}'
                )
            )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Recommandations générées pour {users.count()} utilisateurs'
            )
        )