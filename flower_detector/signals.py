from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import FlowerPrediction, UserStatistics
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=FlowerPrediction)
def update_user_stats(sender, instance, created, **kwargs):
    """Mettre à jour les statistiques après chaque prédiction"""
    if created and instance.user:
        stats, _ = UserStatistics.objects.get_or_create(user=instance.user)
        stats.update_statistics()
        
        # Vérifier les nouveaux achievements
        from .views import check_and_unlock_achievements
        check_and_unlock_achievements(instance.user)


@receiver(post_save, sender=User)
def create_user_dependencies(sender, instance, created, **kwargs):
    """
    Créer automatiquement les dépendances pour chaque nouvel utilisateur
    MAIS ne pas créer le UserProfile (il sera créé manuellement avec le bon rôle)
    """
    if created:
        # Créer UNIQUEMENT les statistiques automatiquement
        UserStatistics.objects.get_or_create(user=instance)
        
        # NE PAS créer le UserProfile ici !
        # Il sera créé dans register_view avec le rôle approprié


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarder le profil s'il existe déjà"""
    # Ne créer le profil QUE s'il n'existe pas et que ce n'est pas une nouvelle création
    if hasattr(instance, 'profile'):
        instance.profile.save()