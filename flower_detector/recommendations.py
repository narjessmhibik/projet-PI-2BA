from collections import Counter
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import FlowerPrediction, FlowerRecommendation, UserFlowerInteraction, FlowerInfo
import random

class FlowerRecommendationEngine:
    
    FLOWER_SIMILARITY = {
        'rose': ['tulipe', 'marguerite'],
        'tulipe': ['rose', 'marguerite'],
        'marguerite': ['tournesol', 'pissenlit'],
        'tournesol': ['marguerite', 'pissenlit'],
        'pissenlit': ['tournesol', 'marguerite'],
    }
    
    # 
    RECOMMENDATION_REASONS = {
        'similar': "Cette fleur ressemble à {flower} que tu as déjà identifiée ! 🌸",
        'popular': "Les élèves adorent cette fleur ! C'est la plus scannée 🏆",
        'new': "Découvre {flower}, parfait pour enrichir ta collection ! 🌺",
        'beginner': "Idéale pour débuter ton exploration botanique ! 🌱",
        'complete': "Pour compléter ta collection de fleurs ! 📚",
    }
    
    def __init__(self, user):
        self.user = user
    
    def normalize_flower_name(self, name):
        """Normalise le nom (minuscules, sans espaces)"""
        normalized = name.lower().strip()
        print(f"[DEBUG] normalize_flower_name: '{name}' → '{normalized}'")
        return normalized
    
    def get_available_flowers(self):
        """Récupère SEULEMENT les fleurs de FlowerInfo"""
        flowers = list(FlowerInfo.objects.values_list('name', flat=True))
        normalized = [self.normalize_flower_name(f) for f in flowers]
        print(f"[DEBUG] get_available_flowers: {normalized}")
        return normalized
    
    def get_user_flower_history(self, days=90):
        """Récupère l'historique des fleurs de l'utilisateur"""
        since = timezone.now() - timedelta(days=days)
        predictions = FlowerPrediction.objects.filter(
            user=self.user,
            created_at__gte=since
        ).values_list('predicted_class', flat=True)
        
        # 🔧 CORRECTION : Normaliser AVANT de retourner
        normalized = [self.normalize_flower_name(f) for f in predictions]
        print(f"[DEBUG] get_user_flower_history: {normalized}")
        return normalized
    
    def get_user_favorites(self):
        """Récupère les 3 fleurs préférées"""
        flowers = self.get_user_flower_history()
        if not flowers:
            print("[DEBUG] get_user_favorites: Aucune fleur dans l'historique")
            return []
        
        flower_counts = Counter(flowers)
        favorites = [flower for flower, count in flower_counts.most_common(3)]
        print(f"[DEBUG] get_user_favorites: {favorites}")
        return favorites
    
    def get_similar_flowers(self, flower_name):
        """Trouve des fleurs similaires"""
        normalized = self.normalize_flower_name(flower_name)
        similar = self.FLOWER_SIMILARITY.get(normalized, [])
        
        # Filtrer pour ne garder que les fleurs disponibles
        available = self.get_available_flowers()
        filtered = [f for f in similar if f in available]
        print(f"[DEBUG] get_similar_flowers({flower_name}): {filtered}")
        return filtered
    
    def get_unexplored_flowers(self):
        """Fleurs non encore scannées"""
        user_flowers = set(self.get_user_flower_history())
        all_flowers = set(self.get_available_flowers())
        unexplored = list(all_flowers - user_flowers)
        
        # 🔧 DEBUG
        print(f"[DEBUG] get_unexplored_flowers:")
        print(f"  → Fleurs utilisateur: {user_flowers}")
        print(f"  → Fleurs disponibles: {all_flowers}")
        print(f"  → Fleurs non explorées: {unexplored}")
        
        return sorted(unexplored)
    
    def get_popular_flowers(self, limit=3):
        """Récupère les fleurs populaires (7 derniers jours)"""
        last_week = timezone.now() - timedelta(days=7)
        popular = FlowerPrediction.objects.filter(
            created_at__gte=last_week
        ).values('predicted_class').annotate(
            count=Count('predicted_class')
        ).order_by('-count')[:limit]
        
        normalized = [self.normalize_flower_name(item['predicted_class']) for item in popular]
        print(f"[DEBUG] get_popular_flowers: {normalized}")
        return normalized
    
    def calculate_confidence_score(self, flower, reason_type):
        """Calcule un score de confiance (0-1)"""
        base_scores = {
            'similar': 0.95,
            'popular': 0.85,
            'beginner': 0.90,
            'new': 0.75,
            'complete': 0.70,
        }
        
        # Bonus d'activité
        user_predictions_count = FlowerPrediction.objects.filter(user=self.user).count()
        activity_bonus = min(0.05, user_predictions_count / 100)
        
        score = base_scores.get(reason_type, 0.7) + activity_bonus
        print(f"[DEBUG] calculate_confidence_score({flower}, {reason_type}): {score:.2f}")
        return score
    
    def generate_recommendations(self, num_recommendations=5):
        """Génère des recommandations personnalisées"""
        print("\n" + "="*60)
        print(f"[DEBUG] GÉNÉRATION DE RECOMMANDATIONS POUR {self.user.username}")
        print("="*60)
        
        recommendations = []
        user_favorites = self.get_user_favorites()
        unexplored = self.get_unexplored_flowers()
        popular = self.get_popular_flowers()
        
        # Si toutes les fleurs sont explorées
        if not unexplored:
            print("[DEBUG] ❌ TOUTES LES FLEURS ONT ÉTÉ EXPLORÉES")
            return []
        
        print(f"[DEBUG] Fleurs non explorées disponibles: {unexplored}")
        
        # 1. Recommandations basées sur les favoris (fleurs similaires)
        print("\n[DEBUG] ÉTAPE 1: Recommandations par similarité")
        if user_favorites:
            for favorite in user_favorites[:2]:
                similar_flowers = self.get_similar_flowers(favorite)
                for similar in similar_flowers:
                    if similar not in [r['flower'] for r in recommendations] and similar in unexplored:
                        print(f"[DEBUG] ✅ Ajout: {similar} (similaire à {favorite})")
                        recommendations.append({
                            'flower': similar,
                            'reason': self.RECOMMENDATION_REASONS['similar'].format(
                                flower=favorite.capitalize()
                            ),
                            'reason_type': 'similar',
                            'confidence': self.calculate_confidence_score(similar, 'similar')
                        })
                        if len(recommendations) >= num_recommendations:
                            break
                if len(recommendations) >= num_recommendations:
                    break
        else:
            print("[DEBUG] Pas de favoris → skip")
        
        # 2. Fleurs populaires non explorées
        print("\n[DEBUG] ÉTAPE 2: Recommandations populaires")
        if len(recommendations) < num_recommendations and popular:
            for flower in popular:
                if flower not in [r['flower'] for r in recommendations] and flower in unexplored:
                    print(f"[DEBUG] ✅ Ajout: {flower} (populaire)")
                    recommendations.append({
                        'flower': flower,
                        'reason': self.RECOMMENDATION_REASONS['popular'],
                        'reason_type': 'popular',
                        'confidence': self.calculate_confidence_score(flower, 'popular')
                    })
                    if len(recommendations) >= num_recommendations:
                        break
        else:
            print("[DEBUG] Pas de fleurs populaires ou quota atteint → skip")
        
        # 3. Recommandations pour débutants (si < 5 prédictions)
        print("\n[DEBUG] ÉTAPE 3: Recommandations débutants")
        total_predictions = FlowerPrediction.objects.filter(user=self.user).count()
        print(f"[DEBUG] Total prédictions: {total_predictions}")
        
        if len(recommendations) < num_recommendations and total_predictions < 5:
            beginner_flowers = ['marguerite', 'tournesol', 'rose']
            available = self.get_available_flowers()
            
            for flower in beginner_flowers:
                if flower in available and flower not in [r['flower'] for r in recommendations] and flower in unexplored:
                    print(f"[DEBUG] ✅ Ajout: {flower} (débutant)")
                    recommendations.append({
                        'flower': flower,
                        'reason': self.RECOMMENDATION_REASONS['beginner'],
                        'reason_type': 'beginner',
                        'confidence': self.calculate_confidence_score(flower, 'beginner')
                    })
                    if len(recommendations) >= num_recommendations:
                        break
        else:
            print("[DEBUG] Utilisateur expérimenté ou quota atteint → skip")
        
        # 4. Compléter avec les fleurs restantes
        print("\n[DEBUG] ÉTAPE 4: Compléter avec fleurs restantes")
        if len(recommendations) < num_recommendations:
            remaining = [f for f in unexplored if f not in [r['flower'] for r in recommendations]]
            random.shuffle(remaining)
            
            for flower in remaining[:num_recommendations - len(recommendations)]:
                print(f"[DEBUG] ✅ Ajout: {flower} (découverte)")
                recommendations.append({
                    'flower': flower,
                    'reason': self.RECOMMENDATION_REASONS['new'].format(
                        flower=flower.capitalize()
                    ),
                    'reason_type': 'new',
                    'confidence': self.calculate_confidence_score(flower, 'new')
                })
        
        # Trier par score de confiance
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"\n[DEBUG] ✅ TOTAL RECOMMANDATIONS GÉNÉRÉES: {len(recommendations)}")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec['flower']} ({rec['confidence']*100:.0f}%)")
        print("="*60 + "\n")
        
        return recommendations[:num_recommendations]
    
    def save_recommendations(self):
        """Sauvegarde les recommandations dans la base de données"""
        # Supprimer les anciennes recommandations non vues (> 7 jours)
        old_date = timezone.now() - timedelta(days=7)
        deleted_count = FlowerRecommendation.objects.filter(
            user=self.user,
            is_viewed=False,
            created_at__lt=old_date
        ).delete()[0]
        
        print(f"[DEBUG] Anciennes recommandations supprimées: {deleted_count}")
        
        # Générer nouvelles recommandations
        recommendations = self.generate_recommendations()
        
        # Sauvegarder dans la base de données
        saved_count = 0
        for rec in recommendations:
            # Vérifier si existe déjà
            existing = FlowerRecommendation.objects.filter(
                user=self.user,
                recommended_flower=rec['flower'],
                is_viewed=False
            ).first()
            
            if not existing:
                FlowerRecommendation.objects.create(
                    user=self.user,
                    recommended_flower=rec['flower'],
                    reason=rec['reason'],
                    confidence_score=rec['confidence']
                )
                saved_count += 1
                print(f"[DEBUG] ✅ Sauvegardé: {rec['flower']}")
        
        print(f"[DEBUG] Nouvelles recommandations sauvegardées: {saved_count}")
        
        # Retourner les recommandations actuelles
        final_recs = FlowerRecommendation.objects.filter(
            user=self.user,
            is_viewed=False
        ).order_by('-confidence_score')[:5]
        
        print(f"[DEBUG] Recommandations retournées: {final_recs.count()}")
        
        return final_recs


def get_smart_recommendations(user):
    """Fonction helper pour obtenir des recommandations"""
    engine = FlowerRecommendationEngine(user)
    return engine.save_recommendations()