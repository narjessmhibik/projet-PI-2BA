from django.db import models
from django.contrib.auth.models import User
# Ajoutez ces modèles à votre flower_detector/models.py

from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class FlowerRecommendation(models.Model):
    """Stocke les recommandations pour chaque utilisateur"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    recommended_flower = models.CharField(max_length=100)
    reason = models.TextField()  # Pourquoi cette recommandation
    confidence_score = models.FloatField(default=0.0)  # Score de confiance
    is_viewed = models.BooleanField(default=False)
    is_clicked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-confidence_score', '-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.recommended_flower}"


class UserFlowerInteraction(models.Model):
    """Suivi des interactions utilisateur avec les fleurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='flower_interactions')
    flower_name = models.CharField(max_length=100)
    interaction_type = models.CharField(max_length=50, choices=[
        ('prediction', 'Prédiction'),
        ('view_details', 'Voir détails'),
        ('save_favorite', 'Favori'),
        ('quiz', 'Quiz'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        
class UserStatistics(models.Model):
    """Statistiques personnelles de l'utilisateur"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='statistics')
    
    # Compteurs généraux
    total_predictions = models.IntegerField(default=0)
    total_flowers_discovered = models.IntegerField(default=0)
    favorite_flower = models.CharField(max_length=50, blank=True)
    
    # Scores et progression
    accuracy_score = models.FloatField(default=0.0)  # Score moyen de confiance
    streak_days = models.IntegerField(default=0)  # Jours consécutifs d'utilisation
    last_activity_date = models.DateField(auto_now=True)
    
    # Préférences détectées (pour recommandations)
    preferred_colors = models.JSONField(default=list)  # ['rouge', 'jaune']
    preferred_families = models.JSONField(default=list)  # ['Rosaceae', 'Asteraceae']
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "User Statistics"
    
    def __str__(self):
        return f"Stats de {self.user.username}"
    
    def update_statistics(self):
        """Mettre à jour les statistiques de l'utilisateur"""
        from django.db.models import Avg
        
        predictions = self.user.predictions.all()
        
        # Compteurs
        self.total_predictions = predictions.count()
        self.total_flowers_discovered = predictions.values('predicted_class').distinct().count()
        
        # Fleur favorite (la plus fréquente)
        favorite = predictions.values('predicted_class') \
            .annotate(count=Count('id')) \
            .order_by('-count') \
            .first()
        
        if favorite:
            self.favorite_flower = favorite['predicted_class']
        
        # Score de confiance moyen
        avg_confidence = predictions.aggregate(Avg('confidence'))['confidence__avg']
        self.accuracy_score = avg_confidence if avg_confidence else 0.0
        
        # Calculer le streak
        self.calculate_streak()
        
        # Analyser les préférences
        self.analyze_preferences()
        
        self.save()
    
    def calculate_streak(self):
        """Calculer le nombre de jours consécutifs d'utilisation"""
        predictions = self.user.predictions.order_by('-created_at')
        
        if not predictions.exists():
            self.streak_days = 0
            return
        
        streak = 1
        current_date = timezone.now().date()
        
        for prediction in predictions:
            pred_date = prediction.created_at.date()
            
            if pred_date == current_date or pred_date == current_date - timedelta(days=streak):
                streak += 1
                current_date = pred_date
            else:
                break
        
        self.streak_days = streak
    
    def analyze_preferences(self):
        """Analyser les préférences de l'utilisateur"""
        from collections import Counter
        
        predictions = self.user.predictions.all()
        
        # Analyser les couleurs préférées
        colors = []
        families = []
        
        for pred in predictions:
            try:
                flower_info = FlowerInfo.objects.get(name=pred.predicted_class.lower())
                colors.extend(flower_info.get_colors_list())
                if flower_info.family:
                    families.append(flower_info.family)
            except FlowerInfo.DoesNotExist:
                pass
        
        # Top 3 couleurs
        color_counter = Counter(colors)
        self.preferred_colors = [color for color, _ in color_counter.most_common(3)]
        
        # Top 3 familles
        family_counter = Counter(families)
        self.preferred_families = [family for family, _ in family_counter.most_common(3)]


class DailyAnalytics(models.Model):
    """Analytics quotidiennes globales"""
    date = models.DateField(unique=True)
    
    # Statistiques quotidiennes
    total_predictions = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    
    # Répartition par fleur
    flower_counts = models.JSONField(default=dict)  # {"rose": 45, "tulipe": 23}
    
    # Métriques de qualité
    average_confidence = models.FloatField(default=0.0)
    high_confidence_count = models.IntegerField(default=0)  # > 90%
    low_confidence_count = models.IntegerField(default=0)   # < 70%
    
    # Engagement
    new_users = models.IntegerField(default=0)
    returning_users = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Daily Analytics"
    
    def __str__(self):
        return f"Analytics du {self.date}"
    
    @classmethod
    def generate_for_date(cls, date=None):
        """Générer les analytics pour une date donnée"""
        if date is None:
            date = timezone.now().date()
        
        # Prédictions du jour
        predictions = FlowerPrediction.objects.filter(
            created_at__date=date
        )
        
        # Créer ou mettre à jour
        analytics, created = cls.objects.get_or_create(date=date)
        
        analytics.total_predictions = predictions.count()
        analytics.unique_users = predictions.values('user').distinct().count()
        
        # Compter par fleur
        flower_counts = {}
        for flower in predictions.values('predicted_class').annotate(count=Count('id')):
            flower_counts[flower['predicted_class']] = flower['count']
        
        analytics.flower_counts = flower_counts
        
        # Métriques de confiance
        confidences = predictions.values_list('confidence', flat=True)
        if confidences:
            analytics.average_confidence = sum(confidences) / len(confidences)
            analytics.high_confidence_count = sum(1 for c in confidences if c > 90)
            analytics.low_confidence_count = sum(1 for c in confidences if c < 70)
        
        # Nouveaux vs returning users
        users_today = set(predictions.values_list('user_id', flat=True))
        new_users = 0
        
        for user_id in users_today:
            first_prediction = FlowerPrediction.objects.filter(user_id=user_id).first()
            if first_prediction and first_prediction.created_at.date() == date:
                new_users += 1
        
        analytics.new_users = new_users
        analytics.returning_users = analytics.unique_users - new_users
        
        analytics.save()
        return analytics


class Achievement(models.Model):
    """Badges et achievements"""
    CATEGORY_CHOICES = [
        ('beginner', 'Débutant'),
        ('explorer', 'Explorateur'),
        ('expert', 'Expert'),
        ('social', 'Social'),
        ('streak', 'Régularité'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    icon = models.CharField(max_length=10, default='🏆')  # Emoji
    
    # Conditions pour débloquer
    requirement_type = models.CharField(max_length=50)  # 'total_predictions', 'streak', etc.
    requirement_value = models.IntegerField()
    
    points = models.IntegerField(default=10)
    
    class Meta:
        ordering = ['category', 'requirement_value']
    
    def __str__(self):
        return f"{self.icon} {self.name}"


class UserAchievement(models.Model):
    """Achievements débloqués par les utilisateurs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'achievement']
        ordering = ['-unlocked_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"
class FlowerPrediction(models.Model):
    """Prédiction de fleur associée à un utilisateur"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='predictions',
        null=True,  # Pour compatibilité avec anciennes données
        blank=True
    )
    image = models.ImageField(upload_to='uploaded_images/')
    predicted_class = models.CharField(max_length=50)
    confidence = models.FloatField()
    description = models.TextField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        username = self.user.username if self.user else "Anonyme"
        return f"{username} - {self.predicted_class} ({self.confidence:.2f}%)"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Prédiction de fleur"
        verbose_name_plural = "Prédictions de fleurs"


class FlowerInfo(models.Model):
    """Informations encyclopédiques sur chaque espèce de fleur"""
    
    # Informations de base
    name = models.CharField(max_length=100, unique=True)
    scientific_name = models.CharField(max_length=200)
    common_names = models.TextField(
        help_text="Noms communs séparés par des virgules",
        blank=True
    )
    
    # Classification botanique
    family = models.CharField(max_length=100)
    genus = models.CharField(max_length=100, blank=True)
    origin = models.CharField(max_length=200)
    
    # Caractéristiques
    colors = models.CharField(
        max_length=200, 
        help_text="Couleurs séparées par des virgules",
        blank=True
    )
    height_min = models.FloatField(help_text="Hauteur minimale en cm")
    height_max = models.FloatField(help_text="Hauteur maximale en cm")
    
    # Période de floraison
    blooming_start = models.CharField(max_length=20)
    blooming_end = models.CharField(max_length=20)
    blooming_description = models.TextField()
    
    # Conditions de culture
    sunlight = models.CharField(max_length=50, choices=[
        ('full_sun', 'Plein soleil'),
        ('partial_shade', 'Mi-ombre'),
        ('shade', 'Ombre'),
        ('adaptable', 'Adaptable'),
    ])
    water_needs = models.CharField(max_length=50, choices=[
        ('low', 'Faibles'),
        ('moderate', 'Modérés'),
        ('high', 'Élevés'),
    ])
    soil_type = models.CharField(max_length=200)
    hardiness_zone = models.CharField(max_length=50, blank=True)
    
    # Conseils d'entretien
    planting_tips = models.TextField(
        help_text="Conseils de plantation",
        blank=True
    )
    care_instructions = models.TextField(
        help_text="Instructions d'entretien",
        blank=True
    )
    pruning_advice = models.TextField(
        help_text="Conseils de taille",
        blank=True
    )
    common_pests = models.TextField(
        help_text="Parasites courants et solutions",
        blank=True
    )
    
    # Utilisations
    medicinal_uses = models.TextField(
        blank=True, 
        help_text="Utilisations médicinales"
    )
    culinary_uses = models.TextField(
        blank=True, 
        help_text="Utilisations culinaires"
    )
    aromatic_properties = models.TextField(
        blank=True, 
        help_text="Propriétés aromatiques"
    )
    other_uses = models.TextField(
        blank=True, 
        help_text="Autres utilisations"
    )
    
    # Informations supplémentaires
    symbolism = models.TextField(
        blank=True, 
        help_text="Symbolique et signification"
    )
    fun_facts = models.TextField(
        blank=True, 
        help_text="Faits intéressants"
    )
    toxicity = models.TextField(
        blank=True, 
        help_text="Informations sur la toxicité"
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Information de fleur"
        verbose_name_plural = "Informations des fleurs"
    
    def __str__(self):
        return f"{self.name.capitalize()} ({self.scientific_name})"
    
    def get_blooming_period(self):
        return f"{self.blooming_start} à {self.blooming_end}"
    
    def get_common_names_list(self):
        if self.common_names:
            return [name.strip() for name in self.common_names.split(',')]
        return []
    
    def get_colors_list(self):
        if self.colors:
            return [color.strip() for color in self.colors.split(',')]
        return []
    
    # ==========================================
# SYSTÈME ENSEIGNANT/ÉTUDIANT
# ==========================================

class UserProfile(models.Model):
    """Profil utilisateur étendu avec rôle"""
    ROLE_CHOICES = [
        ('student', 'Étudiant'),
        ('teacher', 'Enseignant'),
        ('admin', 'Administrateur'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    
    # Pour les étudiants
    teacher = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='students',
        limit_choices_to={'profile__role': 'teacher'}
    )
    
    # Informations supplémentaires
    institution = models.CharField(max_length=200, blank=True)
    class_name = models.CharField(max_length=100, blank=True, verbose_name="Classe")
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def is_student(self):
        return self.role == 'student'
    
    def get_students(self):
        """Retourne les étudiants de cet enseignant"""
        if self.is_teacher():
            return User.objects.filter(profile__teacher=self.user)
        return User.objects.none()


class ClassGroup(models.Model):
    """Groupe/Classe d'étudiants"""
    name = models.CharField(max_length=100)
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='classes',
        limit_choices_to={'profile__role': 'teacher'}
    )
    students = models.ManyToManyField(
        User, 
        related_name='student_classes',
        blank=True,
        limit_choices_to={'profile__role': 'student'}
    )
    
    description = models.TextField(blank=True)
    code = models.CharField(max_length=20, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Classe"
        verbose_name_plural = "Classes"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.teacher.username}"
    
    def save(self, *args, **kwargs):
        # Générer un code unique si vide
        if not self.code:
            import random
            import string
            self.code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)
    
    def get_student_count(self):
        return self.students.count()
    
    def get_class_statistics(self):
        """Statistiques de la classe"""
        students = self.students.all()
        total_predictions = FlowerPrediction.objects.filter(user__in=students).count()
        avg_confidence = FlowerPrediction.objects.filter(user__in=students).aggregate(
            Avg('confidence')
        )['confidence__avg'] or 0
        
        return {
            'student_count': students.count(),
            'total_predictions': total_predictions,
            'avg_confidence': round(avg_confidence, 2),
        }

# Ajoutez ces imports en haut
from django.utils import timezone
from datetime import timedelta

# ==========================================
# SÉQUENCES PÉDAGOGIQUES
# ==========================================

class LearningPath(models.Model):
    """Parcours d'apprentissage créé par l'enseignant"""
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('archived', 'Archivé'),
    ]
    
    DIFFICULTY_CHOICES = [
        ('beginner', 'Débutant'),
        ('intermediate', 'Intermédiaire'),
        ('advanced', 'Avancé'),
    ]
    
    teacher = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='learning_paths'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(
        max_length=20, 
        choices=DIFFICULTY_CHOICES, 
        default='beginner'
    )
    
    # Classes concernées
    class_groups = models.ManyToManyField(
        ClassGroup, 
        related_name='learning_paths',
        blank=True
    )
    
    # Fleurs à identifier (dans l'ordre)
    flowers_sequence = models.JSONField(
        default=list,
        help_text="Liste ordonnée des fleurs: ['rose', 'tulipe', 'marguerite']"
    )
    
    # Objectifs pédagogiques
    learning_objectives = models.TextField(
        blank=True,
        help_text="Objectifs d'apprentissage de ce parcours"
    )
    
    # Configuration
    estimated_duration = models.IntegerField(
        default=30,
        help_text="Durée estimée en minutes"
    )
    points_reward = models.IntegerField(
        default=100,
        help_text="Points XP gagnés en complétant le parcours"
    )
    
    # Dates
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    
    # Statut
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft'
    )
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Parcours d'apprentissage"
        verbose_name_plural = "Parcours d'apprentissage"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.teacher.username}"
    
    def get_flowers_count(self):
        """Nombre de fleurs dans le parcours"""
        return len(self.flowers_sequence)
    
    def get_enrolled_students_count(self):
        """Nombre d'étudiants inscrits"""
        return PathProgress.objects.filter(path=self).values('student').distinct().count()
    
    def get_completion_rate(self):
        """Taux de completion global"""
        total = PathProgress.objects.filter(path=self).count()
        if total == 0:
            return 0
        completed = PathProgress.objects.filter(path=self, is_completed=True).count()
        return round((completed / total) * 100, 1)
    
    def is_available(self):
        """Vérifier si le parcours est disponible"""
        if self.status != 'active':
            return False
        
        today = timezone.now().date()
        
        if self.start_date and today < self.start_date:
            return False
        
        if self.end_date and today > self.end_date:
            return False
        
        return True


class PathProgress(models.Model):
    """Progression d'un étudiant dans un parcours"""
    student = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='path_progress'
    )
    path = models.ForeignKey(
        LearningPath, 
        on_delete=models.CASCADE,
        related_name='progress_records'
    )
    
    # Progression
    completed_flowers = models.JSONField(
        default=list,
        help_text="Liste des fleurs complétées: ['rose', 'tulipe']"
    )
    
    current_step = models.IntegerField(
        default=0,
        help_text="Index de l'étape actuelle (0-based)"
    )
    
    progress_percentage = models.IntegerField(default=0)
    
    # Suivi détaillé
    attempts_log = models.JSONField(
        default=list,
        help_text="Historique des tentatives avec timestamps"
    )
    
    # Statut
    is_completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Score
    total_score = models.IntegerField(default=0)
    average_confidence = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ['student', 'path']
        verbose_name = "Progression de parcours"
        verbose_name_plural = "Progressions de parcours"
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.student.username} - {self.path.title} ({self.progress_percentage}%)"
    
    def update_progress(self, flower_name, confidence, prediction_id):
        """Mettre à jour la progression après une identification"""
        
        # Vérifier si c'est la bonne fleur
        if self.current_step >= len(self.path.flowers_sequence):
            return False, "Parcours déjà complété"
        
        expected_flower = self.path.flowers_sequence[self.current_step]
        
        if flower_name.lower() != expected_flower.lower():
            # Mauvaise fleur identifiée
            self.attempts_log.append({
                'timestamp': timezone.now().isoformat(),
                'expected': expected_flower,
                'identified': flower_name,
                'confidence': confidence,
                'success': False,
                'prediction_id': prediction_id
            })
            self.save()
            return False, f"Fleur incorrecte. Cherchez une {expected_flower} !"
        
        # Bonne fleur !
        self.completed_flowers.append(flower_name)
        self.current_step += 1
        self.total_score += int(confidence)
        
        # Log de la tentative réussie
        self.attempts_log.append({
            'timestamp': timezone.now().isoformat(),
            'flower': flower_name,
            'confidence': confidence,
            'success': True,
            'prediction_id': prediction_id
        })
        
        # Calculer le pourcentage
        self.progress_percentage = int((self.current_step / len(self.path.flowers_sequence)) * 100)
        
        # Calculer la confiance moyenne
        if self.completed_flowers:
            confidences = [log['confidence'] for log in self.attempts_log if log['success']]
            self.average_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        # Vérifier si complété
        if self.current_step >= len(self.path.flowers_sequence):
            self.is_completed = True
            self.completed_at = timezone.now()
            
            # Ajouter des points XP à l'étudiant
            if hasattr(self.student, 'statistics'):
                # Bonus pour la complétion
                self.total_score += self.path.points_reward
        
        self.save()
        
        return True, "Bravo ! Fleur correcte !"
    
    def get_next_flower(self):
        """Obtenir la prochaine fleur à identifier"""
        if self.current_step >= len(self.path.flowers_sequence):
            return None
        return self.path.flowers_sequence[self.current_step]
    
    def get_remaining_flowers(self):
        """Obtenir la liste des fleurs restantes"""
        return self.path.flowers_sequence[self.current_step:]
    
    def get_time_spent(self):
        """Calculer le temps passé"""
        if self.is_completed and self.completed_at:
            delta = self.completed_at - self.started_at
        else:
            delta = timezone.now() - self.started_at
        
        return delta


class PathStep(models.Model):
    """Étape détaillée d'un parcours (optionnel pour instructions)"""
    path = models.ForeignKey(
        LearningPath,
        on_delete=models.CASCADE,
        related_name='steps'
    )
    order = models.IntegerField(default=0)
    flower_name = models.CharField(max_length=100)
    
    # Instructions pour l'étudiant
    instructions = models.TextField(
        blank=True,
        help_text="Consignes pour trouver cette fleur"
    )
    
    hints = models.TextField(
        blank=True,
        help_text="Indices pour aider l'étudiant"
    )
    
    # Points
    points = models.IntegerField(default=10)
    
    # Ressources
    help_image = models.ImageField(
        upload_to='path_steps/',
        blank=True,
        null=True,
        help_text="Image d'aide pour identifier la fleur"
    )
    
    help_video_url = models.URLField(
        blank=True,
        help_text="Lien vers une vidéo d'aide"
    )
    
    class Meta:
        ordering = ['order']
        unique_together = ['path', 'order']
    
    def __str__(self):
        return f"Étape {self.order + 1}: {self.flower_name}"