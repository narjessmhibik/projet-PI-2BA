import os
import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .forms import FlowerImageForm
from .models import FlowerPrediction, FlowerInfo
from .ml_model.predictor import get_predictor
# Ajoutez ces vues à votre flower_detector/views.py

from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Q
from datetime import timedelta
from .models import (
    FlowerPrediction, UserStatistics, DailyAnalytics, 
    Achievement, UserAchievement, FlowerInfo
)
from .models import (
    FlowerPrediction, FlowerInfo, UserStatistics, DailyAnalytics, 
    Achievement, UserAchievement, UserProfile, ClassGroup,     LearningPath,  
    PathProgress # AJOUTEZ CETTE LIGNE
   
)
from  django.shortcuts import render
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .recommendations import FlowerRecommendationEngine, get_smart_recommendations
from .models import FlowerRecommendation

@login_required
def recommendations_view(request):
    """Page de recommandations personnalisées"""
    recommendations = get_smart_recommendations(request.user)
    
    context = {
        'recommendations': recommendations,
        'total_predictions': FlowerPrediction.objects.filter(user=request.user).count(),
    }
    
    # 🔧 CHANGEZ CETTE LIGNE
    return render(request, 'flower_detector/recommendations.html', context)
    # Au lieu de : return render(request, 'recommendations.html', context)
@login_required
def recommendation_click(request, recommendation_id):
    """Enregistre le clic sur une recommandation"""
    try:
        recommendation = FlowerRecommendation.objects.get(id=recommendation_id, user=request.user)
        recommendation.is_clicked = True
        recommendation.is_viewed = True
        recommendation.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Bonne découverte de {recommendation.recommended_flower} ! 🌸'
        })
    except FlowerRecommendation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Recommandation non trouvée'}, status=404)


@login_required
def refresh_recommendations(request):
    """Rafraîchit les recommandations"""
    if request.method == 'POST':
        recommendations = get_smart_recommendations(request.user)
        
        return JsonResponse({
            'success': True,
            'count': recommendations.count(),
            'message': 'Recommandations mises à jour ! 🎉'
        })
    
    return JsonResponse({'success': False}, status=400)


@login_required
def recommendations_api(request):
    """API pour obtenir les recommandations (pour AJAX)"""
    recommendations = FlowerRecommendation.objects.filter(
        user=request.user,
        is_viewed=False
    ).order_by('-confidence_score')[:5]
    
    data = [{
        'id': rec.id,
        'flower': rec.recommended_flower,
        'reason': rec.reason,
        'confidence': round(rec.confidence_score * 100, 1),
        'created_at': rec.created_at.strftime('%d/%m/%Y')
    } for rec in recommendations]
    
    return JsonResponse({'recommendations': data})

def offline_view(request):
    """Page affichée quand pas de connexion"""
    return render(request, 'flower_detector/offline.html')


@login_required
def dashboard(request):
    """Tableau de bord analytics principal"""
    
    # Créer ou récupérer les statistiques de l'utilisateur
    stats, created = UserStatistics.objects.get_or_create(user=request.user)
    
    if created or not stats.updated_at or \
       (timezone.now() - stats.updated_at).seconds > 300:  # Mettre à jour si > 5 min
        stats.update_statistics()
    
    # Statistiques récentes (7 derniers jours)
    week_ago = timezone.now() - timedelta(days=7)
    recent_predictions = FlowerPrediction.objects.filter(
        user=request.user,
        created_at__gte=week_ago
    )
    
    # Compteurs
    predictions_this_week = recent_predictions.count()
    
    # Distribution par fleur (toutes les prédictions)
    flower_distribution = FlowerPrediction.objects.filter(user=request.user) \
        .values('predicted_class') \
        .annotate(count=Count('id')) \
        .order_by('-count')
    
    # Évolution dans le temps (30 derniers jours)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_activity = []
    
    for i in range(30):
        date = (timezone.now() - timedelta(days=29-i)).date()
        count = FlowerPrediction.objects.filter(
            user=request.user,
            created_at__date=date
        ).count()
        daily_activity.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    
    # Confiance moyenne par fleur
    confidence_by_flower = FlowerPrediction.objects.filter(user=request.user) \
        .values('predicted_class') \
        .annotate(avg_confidence=Avg('confidence')) \
        .order_by('-avg_confidence')
    
    # Achievements récents
    recent_achievements = UserAchievement.objects.filter(user=request.user) \
        .select_related('achievement') \
        .order_by('-unlocked_at')[:5]
    
    # Vérifier les nouveaux achievements
    check_and_unlock_achievements(request.user)
    
    context = {
        'stats': stats,
        'predictions_this_week': predictions_this_week,
        'flower_distribution': list(flower_distribution),
        'daily_activity': daily_activity,
        'confidence_by_flower': list(confidence_by_flower),
        'recent_achievements': recent_achievements,
    }
    
    return render(request, 'flower_detector/dashboard.html', context)


@login_required
def analytics_api(request):
    """API pour récupérer les données analytics en JSON"""
    
    # Récupérer les paramètres de filtrage
    period = request.GET.get('period', '30')
    flower = request.GET.get('flower', 'all')
    confidence_level = request.GET.get('confidence', 'all')
    
    # Convertir la période en jours
    if period == 'all':
        predictions = FlowerPrediction.objects.filter(user=request.user)
        days = 365  # Pour la timeline
    else:
        try:
            days = int(period)
        except ValueError:
            days = 30
        
        start_date = timezone.now() - timedelta(days=days)
        predictions = FlowerPrediction.objects.filter(
            user=request.user,
            created_at__gte=start_date
        )
    
    # Filtre par type de fleur
    if flower != 'all':
        predictions = predictions.filter(predicted_class=flower)
    
    # Filtre par niveau de confiance
    if confidence_level == 'high':
        predictions = predictions.filter(confidence__gte=90)
    elif confidence_level == 'medium':
        predictions = predictions.filter(confidence__gte=70, confidence__lt=90)
    elif confidence_level == 'low':
        predictions = predictions.filter(confidence__lt=70)
    
    # Calculer les statistiques de base
    total_predictions = predictions.count()
    avg_confidence = predictions.aggregate(Avg('confidence'))['confidence__avg'] or 0
    
    # Calculer la série de jours consécutifs
    streak_days = calculate_user_streak(request.user)
    
    # Prédictions cette semaine
    week_start = timezone.now() - timedelta(days=7)
    predictions_this_week = predictions.filter(created_at__gte=week_start).count()
    
    # Distribution par fleur
    flower_distribution = list(
        predictions.values('predicted_class')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    
    # Confiance moyenne par fleur
    confidence_by_flower = list(
        predictions.values('predicted_class')
        .annotate(avg_confidence=Avg('confidence'))
        .order_by('predicted_class')
    )
    
    # Timeline (activité quotidienne)
    timeline = []
    for i in range(days):
        date = (timezone.now() - timedelta(days=days-1-i)).date()
        count = predictions.filter(created_at__date=date).count()
        timeline.append({
            'date': date.isoformat(),
            'count': count
        })
    
    # Distribution de confiance
    confidence_distribution = {
        'high': predictions.filter(confidence__gte=90).count(),
        'medium': predictions.filter(confidence__gte=70, confidence__lt=90).count(),
        'low': predictions.filter(confidence__lt=70).count(),
    }
    
    # Préparer la réponse JSON
    data = {
        'total': total_predictions,
        'average_confidence': round(avg_confidence, 2),
        'streak_days': streak_days,
        'predictions_this_week': predictions_this_week,
        'flower_distribution': flower_distribution,
        'confidence_by_flower': confidence_by_flower,
        'timeline': timeline,
        'confidence_distribution': confidence_distribution,
    }
    
    return JsonResponse(data)


def calculate_user_streak(user):
    """Calculer la série de jours consécutifs d'utilisation"""
    predictions = FlowerPrediction.objects.filter(user=user).order_by('-created_at')
    
    if not predictions.exists():
        return 0
    
    streak = 0
    current_date = timezone.now().date()
    checked_dates = set()
    
    for prediction in predictions:
        pred_date = prediction.created_at.date()
        
        # Si on a déjà vérifié cette date, on continue
        if pred_date in checked_dates:
            continue
        
        checked_dates.add(pred_date)
        
        # Si la prédiction est aujourd'hui ou hier (série continue)
        if pred_date == current_date or pred_date == current_date - timedelta(days=1):
            if pred_date == current_date - timedelta(days=1) and streak == 0:
                # Si c'est hier et qu'on n'a pas encore compté aujourd'hui
                current_date = pred_date
            
            streak += 1
            current_date = pred_date - timedelta(days=1)
        else:
            # Si on saute un jour, la série est brisée
            break
    
    return streak

@login_required
def global_analytics(request):
    """Analytics globales pour tous les utilisateurs (admin uniquement)"""
    
    if not request.user.is_staff:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    # Statistiques globales
    total_users = User.objects.count()
    total_predictions = FlowerPrediction.objects.count()
    
    # Analytics des 30 derniers jours
    thirty_days = []
    for i in range(30):
        date = (timezone.now() - timedelta(days=29-i)).date()
        analytics = DailyAnalytics.objects.filter(date=date).first()
        
        if analytics:
            thirty_days.append({
                'date': date.isoformat(),
                'predictions': analytics.total_predictions,
                'users': analytics.unique_users,
                'avg_confidence': analytics.average_confidence,
            })
        else:
            # Générer si manquant
            analytics = DailyAnalytics.generate_for_date(date)
            thirty_days.append({
                'date': date.isoformat(),
                'predictions': analytics.total_predictions,
                'users': analytics.unique_users,
                'avg_confidence': analytics.average_confidence,
            })
    
    # Top fleurs
    top_flowers = FlowerPrediction.objects.values('predicted_class') \
        .annotate(count=Count('id')) \
        .order_by('-count')[:10]
    
    # Utilisateurs actifs
    week_ago = timezone.now() - timedelta(days=7)
    active_users = FlowerPrediction.objects.filter(
        created_at__gte=week_ago
    ).values('user').distinct().count()
    
    context = {
        'total_users': total_users,
        'total_predictions': total_predictions,
        'active_users': active_users,
        'thirty_days': thirty_days,
        'top_flowers': list(top_flowers),
    }
    
    return render(request, 'flower_detector/global_analytics.html', context)


def check_and_unlock_achievements(user):
    """Vérifier et débloquer les achievements pour un utilisateur"""
    
    stats, _ = UserStatistics.objects.get_or_create(user=user)
    
    # Récupérer tous les achievements non débloqués
    unlocked_ids = UserAchievement.objects.filter(user=user) \
        .values_list('achievement_id', flat=True)
    
    pending_achievements = Achievement.objects.exclude(id__in=unlocked_ids)
    
    newly_unlocked = []
    
    for achievement in pending_achievements:
        unlocked = False
        
        # Vérifier les conditions
        if achievement.requirement_type == 'total_predictions':
            if stats.total_predictions >= achievement.requirement_value:
                unlocked = True
        
        elif achievement.requirement_type == 'streak':
            if stats.streak_days >= achievement.requirement_value:
                unlocked = True
        
        elif achievement.requirement_type == 'flowers_discovered':
            if stats.total_flowers_discovered >= achievement.requirement_value:
                unlocked = True
        
        elif achievement.requirement_type == 'high_accuracy':
            if stats.accuracy_score >= achievement.requirement_value:
                unlocked = True
        
        # Débloquer si conditions remplies
        if unlocked:
            UserAchievement.objects.create(
                user=user,
                achievement=achievement
            )
            newly_unlocked.append(achievement)
    
    return newly_unlocked


@login_required
def export_analytics_pdf(request):
    """Exporter les analytics en PDF avec graphiques améliorés et lisibles"""
    from django.http import HttpResponse
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.graphics.shapes import Drawing, String
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.charts.legends import Legend
    from io import BytesIO
    from datetime import timedelta
    
    # PDF en format PAYSAGE pour plus d'espace
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=landscape(A4),
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    elements = []
    
    styles = getSampleStyleSheet()
    
    # 🎨 STYLES PERSONNALISÉS
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=32,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=20,
        textColor=colors.HexColor('#8b5cf6'),
        spaceAfter=20,
        spaceBefore=25,
        fontName='Helvetica-Bold',
        borderWidth=2,
        borderColor=colors.HexColor('#6366f1'),
        borderPadding=10,
        backColor=colors.HexColor('#f0f0ff')
    )
    
    # 📊 TITRE PRINCIPAL
    title = Paragraph(f"📊 Rapport d'Analytics - {request.user.username}", title_style)
    elements.append(title)
    
    date_para = Paragraph(
        f"📅 Généré le {timezone.now().strftime('%d/%m/%Y à %H:%M')}",
        ParagraphStyle('DateStyle', parent=styles['Normal'], alignment=TA_CENTER, 
                      textColor=colors.grey, fontSize=12)
    )
    elements.append(date_para)
    elements.append(Spacer(1, 0.4*inch))
    
    # Récupérer les statistiques
    stats = UserStatistics.objects.get(user=request.user)
    
    # ==========================================
    # 📈 SECTION 1 : STATISTIQUES CLÉS
    # ==========================================
    elements.append(Paragraph("📈 Statistiques Globales", subtitle_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # Tableau avec design amélioré
    data = [
        ['🎯 Métrique', '📊 Valeur', '📝 Détails'],
        ['🌺 Prédictions totales', str(stats.total_predictions), 'Toutes analyses confondues'],
        ['🌸 Fleurs découvertes', str(stats.total_flowers_discovered), 'Types différents identifiés'],
        ['💝 Fleur favorite', stats.favorite_flower.capitalize() if stats.favorite_flower else '—', 'Basé sur vos analyses'],
        ['⭐ Score de confiance', f"{stats.accuracy_score:.1f}%", 'Confiance moyenne du modèle'],
        ['🔥 Jours consécutifs', str(stats.streak_days), 'Série actuelle d\'activité'],
    ]
    
    table = Table(data, colWidths=[3*inch, 2*inch, 4*inch])
    table.setStyle(TableStyle([
        # En-tête
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 15),
        ('TOPPADDING', (0, 0), (-1, 0), 15),
        
        # Corps du tableau
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9ff')]),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#6366f1')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # ==========================================
    # 🌺 SECTION 2 : GRAPHIQUE CAMEMBERT AMÉLIORÉ
    # ==========================================
    elements.append(Paragraph("🌺 Distribution par Type de Fleur", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    
    flower_dist = FlowerPrediction.objects.filter(user=request.user) \
        .values('predicted_class') \
        .annotate(count=Count('id')) \
        .order_by('-count')[:6]
    
    if flower_dist:
        total = sum([item['count'] for item in flower_dist])
        
        # 🎨 GRAND GRAPHIQUE EN CAMEMBERT
        drawing = Drawing(700, 350)
        
        # Camembert
        pie = Pie()
        pie.x = 80
        pie.y = 50
        pie.width = 280
        pie.height = 280
        
        # Données
        pie.data = [item['count'] for item in flower_dist]
        pie.labels = [f"{item['predicted_class'].capitalize()}\n{item['count']} ({(item['count']/total*100):.1f}%)" 
                      for item in flower_dist]
        
        # 🎨 Couleurs vives et contrastées
        colors_list = [
            colors.HexColor('#6366f1'),  # Bleu indigo
            colors.HexColor('#ec4899'),  # Rose
            colors.HexColor('#8b5cf6'),  # Violet
            colors.HexColor('#10b981'),  # Vert
            colors.HexColor('#f59e0b'),  # Orange
            colors.HexColor('#ef4444'),  # Rouge
        ]
        
        # Style du camembert
        for i, color in enumerate(colors_list[:len(pie.data)]):
            pie.slices[i].fillColor = color
            pie.slices[i].strokeWidth = 2
            pie.slices[i].strokeColor = colors.white
            pie.slices[i].popout = 8  # Séparation des parts
        
        # Labels plus gros et visibles
        pie.slices.fontSize = 11
        pie.slices.fontName = 'Helvetica-Bold'
        pie.slices.labelRadius = 1.2
        
        drawing.add(pie)
        
        # 📊 LÉGENDE À DROITE
        legend = Legend()
        legend.x = 400
        legend.y = 200
        legend.dx = 15
        legend.dy = 15
        legend.fontName = 'Helvetica-Bold'
        legend.fontSize = 12
        legend.columnMaximum = 6
        legend.alignment = 'right'
        legend.colorNamePairs = [(colors_list[i], 
                                  f"{item['predicted_class'].capitalize()}: {item['count']} ({(item['count']/total*100):.1f}%)")
                                 for i, item in enumerate(flower_dist)]
        
        drawing.add(legend)
        
        # Titre du graphique
        title_text = String(350, 320, 'Répartition des Analyses', 
                           textAnchor='middle', fontSize=16, 
                           fontName='Helvetica-Bold', fillColor=colors.HexColor('#6366f1'))
        drawing.add(title_text)
        
        elements.append(drawing)
    
    elements.append(PageBreak())
    
    # ==========================================
    # ⭐ SECTION 3 : GRAPHIQUE EN BARRES
    # ==========================================
    elements.append(Paragraph("⭐ Score de Confiance par Fleur", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    
    confidence_data = FlowerPrediction.objects.filter(user=request.user) \
        .values('predicted_class') \
        .annotate(avg_confidence=Avg('confidence')) \
        .order_by('-avg_confidence')[:6]
    
    if confidence_data:
        # Grand graphique en barres
        drawing = Drawing(700, 350)
        bc = VerticalBarChart()
        bc.x = 50
        bc.y = 80
        bc.height = 220
        bc.width = 600
        bc.data = [[item['avg_confidence'] for item in confidence_data]]
        bc.categoryAxis.categoryNames = [item['predicted_class'].capitalize() 
                                         for item in confidence_data]
        
        # Style des barres
        bc.bars[0].fillColor = colors.HexColor('#6366f1')
        bc.bars[0].strokeColor = colors.HexColor('#4f46e5')
        bc.bars[0].strokeWidth = 2
        
        # Axes
        bc.valueAxis.valueMin = 0
        bc.valueAxis.valueMax = 100
        bc.valueAxis.valueStep = 10
        bc.valueAxis.labels.fontName = 'Helvetica-Bold'
        bc.valueAxis.labels.fontSize = 11
        bc.valueAxis.labels.dx = -5
        
        bc.categoryAxis.labels.angle = 0
        bc.categoryAxis.labels.fontName = 'Helvetica-Bold'
        bc.categoryAxis.labels.fontSize = 12
        bc.categoryAxis.labels.dy = -5
        
        # Grille
        bc.valueAxis.visibleGrid = True
        bc.valueAxis.gridStrokeColor = colors.HexColor('#e0e0e0')
        
        drawing.add(bc)
        
        # Ajouter les valeurs au-dessus des barres
        for i, item in enumerate(confidence_data):
            value_text = String(
                80 + i * 100, 
                310, 
                f"{item['avg_confidence']:.1f}%",
                textAnchor='middle',
                fontSize=12,
                fontName='Helvetica-Bold',
                fillColor=colors.HexColor('#6366f1')
            )
            drawing.add(value_text)
        
        elements.append(drawing)
        
        # Interprétation
        interpretation = Paragraph(
            f"<b>💡 Analyse :</b> Votre score de confiance moyen global est de <b>{stats.accuracy_score:.1f}%</b>. "
            f"Les fleurs avec un score supérieur à 90% sont très bien maîtrisées !",
            ParagraphStyle('Interp', parent=styles['Normal'], fontSize=12, 
                          backColor=colors.HexColor('#f0f9ff'), borderPadding=10,
                          borderWidth=1, borderColor=colors.HexColor('#6366f1'))
        )
        elements.append(Spacer(1, 0.3*inch))
        elements.append(interpretation)
    
    elements.append(Spacer(1, 0.4*inch))
    
    # ==========================================
    # 📈 SECTION 4 : ACTIVITÉ MENSUELLE
    # ==========================================
    elements.append(Paragraph("📈 Évolution de l'Activité sur 30 Jours", subtitle_style))
    elements.append(Spacer(1, 0.3*inch))
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    daily_predictions = []
    dates_labels = []
    
    for i in range(30):
        date = (timezone.now() - timedelta(days=29-i)).date()
        count = FlowerPrediction.objects.filter(
            user=request.user,
            created_at__date=date
        ).count()
        daily_predictions.append(count)
        dates_labels.append(f"{date.day}/{date.month}")
    
    # Grand graphique linéaire
    drawing = Drawing(700, 280)
    lc = HorizontalLineChart()
    lc.x = 60
    lc.y = 50
    lc.height = 180
    lc.width = 600
    lc.data = [daily_predictions]
    lc.joinedLines = 1
    
    # Style de la ligne
    lc.lines[0].strokeColor = colors.HexColor('#6366f1')
    lc.lines[0].strokeWidth = 3
    lc.lines[0].symbol = None
    
    # Axes
    lc.valueAxis.valueMin = 0
    max_val = max(daily_predictions) if daily_predictions else 5
    lc.valueAxis.valueMax = max_val + 2
    lc.valueAxis.labels.fontName = 'Helvetica'
    lc.valueAxis.labels.fontSize = 10
    lc.valueAxis.visibleGrid = True
    lc.valueAxis.gridStrokeColor = colors.HexColor('#e0e0e0')
    
    # Labels de date (tous les 3 jours)
    step = 3
    lc.categoryAxis.categoryNames = [dates_labels[i] if i % step == 0 else '' 
                                     for i in range(len(dates_labels))]
    lc.categoryAxis.labels.angle = 45
    lc.categoryAxis.labels.fontSize = 9
    lc.categoryAxis.labels.fontName = 'Helvetica'
    
    drawing.add(lc)
    elements.append(drawing)
    
    # Statistiques récapitulatives
    total_30_days = sum(daily_predictions)
    avg_per_day = total_30_days / 30 if total_30_days > 0 else 0
    max_day = max(daily_predictions) if daily_predictions else 0
    
    summary_data = [
        ['📊 Période', '📈 Valeur', '💡 Insight'],
        ['Total sur 30 jours', str(total_30_days), f'{total_30_days} analyses effectuées'],
        ['Moyenne par jour', f"{avg_per_day:.1f}", 'Régularité de votre activité'],
        ['Jour le plus actif', str(max_day), 'Pic d\'activité atteint'],
        ['Tendance', '📈 En progression' if total_30_days > 10 else '📊 Stable', 
         'Continuez vos efforts !'],
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch, 4*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 13),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf5ff')]),
        ('GRID', (0, 0), (-1, -1), 1.5, colors.HexColor('#8b5cf6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(Spacer(1, 0.3*inch))
    elements.append(summary_table)
    
    # Footer stylisé
    elements.append(Spacer(1, 0.6*inch))
    footer_text = Paragraph(
        "🌸 <b>Flower Detector Analytics</b> - Rapport généré automatiquement 🌸<br/>"
        f"<i>Date: {timezone.now().strftime('%d/%m/%Y à %H:%M')}</i>",
        ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_CENTER, 
                      textColor=colors.HexColor('#6366f1'), fontSize=10,
                      borderWidth=1, borderColor=colors.HexColor('#6366f1'),
                      borderPadding=8, backColor=colors.HexColor('#f0f9ff'))
    )
    elements.append(footer_text)
    
    # Construire le PDF
    doc.build(elements)
    
    # Retourner le PDF
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"analytics_{request.user.username}_{timezone.now().strftime('%Y%m%d_%H%M')}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

def home(request):
    recent_predictions = FlowerPrediction.objects.all().order_by('-created_at')[:6]
    stats = {
        'total_analyses': FlowerPrediction.objects.count(),
        'users_count': User.objects.count(),
        'flower_types': 5,
    }
    return render(request, 'flower_detector/home.html', {
        'recent_predictions': recent_predictions,
        'stats': stats,
    })


def register_view(request):
    if request.user.is_authenticated:
        return redirect('flower_detector:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        role = request.POST.get('role')  # Récupérer le rôle
        institution = request.POST.get('institution', '')  # Optionnel

        # Validations
        if not all([username, email, password1, password2, role]):
            messages.error(request, 'Tous les champs obligatoires doivent être remplis.')
            return render(request, 'flower_detector/register.html')

        if role not in ['student', 'teacher']:
            messages.error(request, 'Rôle invalide.')
            return render(request, 'flower_detector/register.html')

        if password1 != password2:
            messages.error(request, 'Les mots de passe ne correspondent pas.')
            return render(request, 'flower_detector/register.html')

        if len(password1) < 6:
            messages.error(request, 'Le mot de passe doit contenir au moins 6 caractères.')
            return render(request, 'flower_detector/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur existe déjà.")
            return render(request, 'flower_detector/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Cet email est déjà utilisé.')
            return render(request, 'flower_detector/register.html')

        try:
            # Créer l'utilisateur
            user = User.objects.create_user(username=username, email=email, password=password1)
            
            # 🆕 Utiliser get_or_create au lieu de create pour éviter les doublons
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'role': role,
                    'institution': institution
                }
            )
            
            # Si le profil existait déjà, mettre à jour le rôle et l'institution
            if not created:
                profile.role = role
                profile.institution = institution
                profile.save()
            
            # Créer les statistiques (get_or_create aussi pour éviter les doublons)
            UserStatistics.objects.get_or_create(user=user)
            
            # Connecter l'utilisateur
            login(request, user)
            
            role_text = "enseignant" if role == 'teacher' else "étudiant"
            messages.success(request, f'Bienvenue {username} ! Vous êtes inscrit en tant que {role_text}.')
            
            # Rediriger selon le rôle
            if role == 'teacher':
                return redirect('flower_detector:teacher_dashboard')
            else:
                return redirect('flower_detector:student_dashboard')
                
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du compte : {str(e)}')
            return render(request, 'flower_detector/register.html')

    return render(request, 'flower_detector/register.html')


@login_required
def teacher_classes(request):
    """Liste de toutes les classes de l'enseignant"""
    
    # Créer le profil s'il n'existe pas
    if not hasattr(request.user, 'profile'):
        UserProfile.objects.create(user=request.user, role='teacher')
    
    profile = request.user.profile
    
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    # Récupérer toutes les classes de l'enseignant
    classes = ClassGroup.objects.filter(teacher=request.user).order_by('-created_at')
    
    # Statistiques pour chaque classe
    classes_with_stats = []
    for class_group in classes:
        stats = class_group.get_class_statistics()
        classes_with_stats.append({
            'class': class_group,
            'stats': stats
        })
    
    context = {
        'classes': classes_with_stats,
    }
    
    return render(request, 'flower_detector/teacher_classes.html', context)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('flower_detector:home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            messages.error(request, 'Veuillez remplir tous les champs.')
            return render(request, 'flower_detector/login.html')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # 🆕 Créer le profil s'il n'existe pas (pour les anciens utilisateurs)
            if not hasattr(user, 'profile'):
                UserProfile.objects.create(user=user, role='student')
            
            # 🆕 Créer les stats si elles n'existent pas
            if not hasattr(user, 'statistics'):
                UserStatistics.objects.create(user=user)
            
            # ✅ CORRECTION : Rediriger vers la page d'accueil
            role = user.profile.role
            role_text = "Professeur" if role == 'teacher' else ""
            
            messages.success(request, f'Bienvenue {role_text} {user.username} !')
            return redirect('flower_detector:home')  # ✅ TOUJOURS VERS HOME

        messages.error(request, "Nom d'utilisateur ou mot de passe incorrect.")

    return render(request, 'flower_detector/login.html')


@login_required
def logout_view(request):
    username = request.user.username
    logout(request)
    messages.success(request, f'Au revoir {username} !')
    return redirect('flower_detector:home')


@login_required
def predict(request):
    if request.method == 'POST':
        form = FlowerImageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                image_file = request.FILES['image']

                media_dir = os.path.join(settings.MEDIA_ROOT, 'uploaded_images')
                os.makedirs(media_dir, exist_ok=True)

                timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{image_file.name}"
                image_path = os.path.join(media_dir, filename)

                with open(image_path, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)

                predictor = get_predictor()
                result = predictor.predict(image_path)

                prediction = FlowerPrediction.objects.create(
                    user=request.user,
                    image=f'uploaded_images/{filename}',
                    predicted_class=result['predicted_class'],
                    confidence=result['confidence'],
                    description=result['description'],
                    note='Mode modèle (ResNet50)'
                )

                messages.success(request, f'Fleur identifiée : {result["predicted_class"].capitalize()}')
                return redirect('flower_detector:result', prediction_id=prediction.id)

            except Exception as e:
                messages.error(request, f"Erreur lors de la prédiction : {str(e)}")

    else:
        form = FlowerImageForm()

    return render(request, 'flower_detector/predict.html', {'form': form})


@login_required
def history(request):
    predictions = FlowerPrediction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'flower_detector/history.html', {'predictions': predictions})


@login_required
def result(request, prediction_id):
    """
    Vue pour afficher les résultats d'une prédiction avec toutes les informations
    de la base de données
    """
    prediction = get_object_or_404(FlowerPrediction, id=prediction_id, user=request.user)
    
    # TRÈS IMPORTANT : convertir en minuscules pour matcher avec la BDD
    flower_name = prediction.predicted_class.lower()
    
    # Récupérer les informations de la fleur depuis la base de données
    try:
        flower_info = FlowerInfo.objects.get(name=flower_name)
        print(f"✅ FlowerInfo trouvée: {flower_info.name} - {flower_info.scientific_name}")
    except FlowerInfo.DoesNotExist:
        flower_info = None
        print(f"❌ Pas d'info pour: {flower_name}")
        print(f"   Fleurs disponibles: {list(FlowerInfo.objects.values_list('name', flat=True))}")
    
    context = {
        'result': prediction,
        'image_url': prediction.image.url,
        'flower_info': flower_info,
        'prediction_id': prediction.id
    }
    
    return render(request, 'flower_detector/result.html', context)


@require_http_methods(["POST"])
@csrf_exempt
def chat_api(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        if not user_message:
            return JsonResponse({'error': 'Message vide'}, status=400)

        demo_responses = [
            "🌸 Je suis un chatbot botanique !",
            "🌺 Téléchargez une image claire de fleur pour une meilleure prédiction.",
            "🌻 Le tournesol est reconnaissable à ses grandes fleurs jaunes.",
        ]

        return JsonResponse({'response': random.choice(demo_responses), 'status': 'demo'})
    except Exception as e:
        return JsonResponse({'error': f'Erreur serveur: {str(e)}'}, status=500)
    
    # ==========================================
# VUES ENSEIGNANT
# ==========================================

@login_required
def teacher_dashboard(request):
    """Tableau de bord enseignant"""
    # Créer le profil s'il n'existe pas
    if not hasattr(request.user, 'profile'):
        UserProfile.objects.create(user=request.user, role='teacher')
    
    profile = request.user.profile
    
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    # Récupérer les classes de l'enseignant
    classes = ClassGroup.objects.filter(teacher=request.user)
    
    # Récupérer tous les étudiants
    all_students = User.objects.filter(
        student_classes__teacher=request.user
    ).distinct()
    
    # Statistiques globales
    total_students = all_students.count()
    total_predictions = FlowerPrediction.objects.filter(user__in=all_students).count()
    
    # Calculer le taux de réussite moyen (confiance > 70%)
    if total_predictions > 0:
        high_confidence = FlowerPrediction.objects.filter(
            user__in=all_students,
            confidence__gte=70
        ).count()
        average_success_rate = round((high_confidence / total_predictions) * 100, 1)
    else:
        average_success_rate = 0
    
    # Top 10 étudiants les plus actifs
    top_students = all_students.annotate(
        prediction_count=Count('predictions')
    ).order_by('-prediction_count')[:10]
    
    # Calculer le taux de réussite pour chaque étudiant
    for student in top_students:
        total = student.prediction_count
        if total > 0:
            high_conf = FlowerPrediction.objects.filter(
                user=student,
                confidence__gte=70
            ).count()
            student.success_rate = round((high_conf / total) * 100, 1)
        else:
            student.success_rate = 0
        
        # Récupérer les classes de l'étudiant
        student.class_groups = student.student_classes.filter(teacher=request.user)
    
    # Activité récente (7 derniers jours)
    week_ago = timezone.now() - timedelta(days=7)
    recent_activity = FlowerPrediction.objects.filter(
        user__in=all_students,
        created_at__gte=week_ago
    ).order_by('-created_at')[:10]
    
    # Distribution des fleurs (toute la classe)
    flower_distribution = FlowerPrediction.objects.filter(
        user__in=all_students
    ).values('predicted_class').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    # Fleurs difficiles (taux de confiance < 70%)
    difficult_flowers_data = FlowerPrediction.objects.filter(
        user__in=all_students
    ).values('predicted_class').annotate(
        total_attempts=Count('id'),
        failed_attempts=Count('id', filter=Q(confidence__lt=70))
    )
    
    difficult_flowers = []
    for item in difficult_flowers_data:
        if item['total_attempts'] > 0:
            failure_rate = (item['failed_attempts'] / item['total_attempts']) * 100
            if failure_rate > 20:  # Plus de 20% d'échec
                difficult_flowers.append({
                    'name': item['predicted_class'],
                    'total_attempts': item['total_attempts'],
                    'failed_attempts': item['failed_attempts'],
                    'failure_rate': round(failure_rate, 1),
                    'students_struggling': FlowerPrediction.objects.filter(
                        user__in=all_students,
                        predicted_class=item['predicted_class'],
                        confidence__lt=70
                    ).values('user').distinct().count()
                })
    
    # Trier par taux d'échec décroissant
    difficult_flowers = sorted(difficult_flowers, key=lambda x: x['failure_rate'], reverse=True)[:5]
    
    # ==================== AJOUT IMPORTANT ====================
    # Liste des mois pour le rapport mensuel (corrigé)
    months = [
        {'value': '2025-01', 'name': 'Janvier'},
        {'value': '2025-02', 'name': 'Février'},
        {'value': '2025-03', 'name': 'Mars'},
        {'value': '2025-04', 'name': 'Avril'},
        {'value': '2025-05', 'name': 'Mai'},
        {'value': '2025-06', 'name': 'Juin'},
        {'value': '2025-07', 'name': 'Juillet'},
        {'value': '2025-08', 'name': 'Août'},
        {'value': '2025-09', 'name': 'Septembre'},
        {'value': '2025-10', 'name': 'Octobre'},
        {'value': '2025-11', 'name': 'Novembre'},
        {'value': '2025-12', 'name': 'Décembre'},
    ]
    
    # Statistiques hebdomadaires pour le graphique
    weekly_stats = []
    for i in range(7):
        day = timezone.now() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        day_count = FlowerPrediction.objects.filter(
            user__in=all_students,
            created_at__gte=day_start,
            created_at__lte=day_end
        ).count()
        
        weekly_stats.append(day_count)
    
    weekly_stats.reverse()  # Pour avoir du lundi à dimanche
    # ==================== FIN DE L'AJOUT ====================
    
    context = {
        'classes': classes,
        'total_students': total_students,
        'total_predictions': total_predictions,
        'average_success_rate': average_success_rate,
        'top_students': top_students,
        'all_students': all_students,
        'recent_activity': recent_activity,
        'flower_distribution': list(flower_distribution),
        'difficult_flowers': difficult_flowers,
        'months': months,  # AJOUTÉ - pour le sélecteur de mois
        'weekly_stats': weekly_stats,  # AJOUTÉ - pour le graphique
    }
    
    return render(request, 'flower_detector/teacher_dashboard.html', context)







@login_required
def student_detail(request, student_id):
    """Détails d'un étudiant (pour l'enseignant)"""
    profile = request.user.profile
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    # Vérifier que l'étudiant appartient à cet enseignant
    student = get_object_or_404(User, id=student_id, profile__teacher=request.user)
    
    # Statistiques de l'étudiant
    stats = student.statistics
    predictions = FlowerPrediction.objects.filter(user=student).order_by('-created_at')
    
    # Activité des 30 derniers jours
    daily_activity = []
    for i in range(30):
        date = (timezone.now() - timedelta(days=29-i)).date()
        count = predictions.filter(created_at__date=date).count()
        daily_activity.append({
            'date': date.strftime('%d/%m'),
            'count': count
        })
    
    # Distribution par fleur
    flower_distribution = predictions.values('predicted_class').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'student': student,
        'stats': stats,
        'predictions': predictions[:10],
        'daily_activity': daily_activity,
        'flower_distribution': list(flower_distribution),
    }
    
    return render(request, 'flower_detector/student_detail.html', context)


@login_required
def create_class(request):
    """Créer une nouvelle classe"""
    profile = request.user.profile
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if not name:
            messages.error(request, "Le nom de la classe est requis.")
        else:
            class_group = ClassGroup.objects.create(
                name=name,
                teacher=request.user,
                description=description
            )
            messages.success(request, f"Classe '{name}' créée avec succès ! Code: {class_group.code}")
            return redirect('flower_detector:teacher_dashboard')
    
    return render(request, 'flower_detector/create_class.html')


@login_required
def class_detail(request, class_id):
    """Détails d'une classe"""
    profile = request.user.profile
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    class_group = get_object_or_404(ClassGroup, id=class_id, teacher=request.user)
    students = class_group.students.all()
    
    # Statistiques de la classe
    class_stats = class_group.get_class_statistics()
    
    # Classement des étudiants
    student_ranking = students.annotate(
        prediction_count=Count('predictions')
    ).order_by('-prediction_count')
    
    context = {
        'class_group': class_group,
        'students': student_ranking,
        'class_stats': class_stats,
    }
    
    return render(request, 'flower_detector/class_detail.html', context)


# ==========================================
# VUES ÉTUDIANT
# ==========================================

@login_required
def student_dashboard(request):
    """Tableau de bord étudiant"""
    profile = request.user.profile
    if not profile.is_student():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('flower_detector:home')
    
    # Statistiques personnelles
    stats = request.user.statistics
    
    # Classes de l'étudiant
    my_classes = request.user.student_classes.all()
    
    # Comparer avec la moyenne de la classe
    if profile.teacher:
        classmates = User.objects.filter(profile__teacher=profile.teacher).exclude(id=request.user.id)
        class_avg_predictions = FlowerPrediction.objects.filter(
            user__in=classmates
        ).values('user').annotate(
            count=Count('id')
        ).aggregate(Avg('count'))['count__avg'] or 0
        
        class_avg_confidence = FlowerPrediction.objects.filter(
            user__in=classmates
        ).aggregate(Avg('confidence'))['confidence__avg'] or 0
    else:
        class_avg_predictions = 0
        class_avg_confidence = 0
    
    # Prédictions récentes
    recent_predictions = FlowerPrediction.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Achievements
    achievements = UserAchievement.objects.filter(
        user=request.user
    ).select_related('achievement').order_by('-unlocked_at')[:3]
    
    context = {
        'stats': stats,
        'my_classes': my_classes,
        'class_avg_predictions': round(class_avg_predictions, 1),
        'class_avg_confidence': round(class_avg_confidence, 1),
        'recent_predictions': recent_predictions,
        'achievements': achievements,
        'teacher': profile.teacher,
    }
    
    return render(request, 'flower_detector/student_dashboard.html', context)


@login_required
def join_class(request):
    """Rejoindre une classe avec un code"""
    profile = request.user.profile
    if not profile.is_student():
        messages.error(request, "Seuls les étudiants peuvent rejoindre une classe.")
        return redirect('flower_detector:home')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        
        try:
            class_group = ClassGroup.objects.get(code=code)
            class_group.students.add(request.user)
            
            # Associer l'étudiant à l'enseignant
            profile.teacher = class_group.teacher
            profile.save()
            
            messages.success(request, f"Vous avez rejoint la classe '{class_group.name}' !")
            return redirect('flower_detector:student_dashboard')
        except ClassGroup.DoesNotExist:
            messages.error(request, "Code de classe invalide.")
    
    return render(request, 'flower_detector/join_class.html')


# ==========================================
# VUES SÉQUENCES PÉDAGOGIQUES - ENSEIGNANT
# ==========================================

@login_required
def learning_paths_list(request):
    """Liste des parcours d'apprentissage de l'enseignant"""
    # Note : Vous utilisez request.user.profile dans votre code original
    # Assurez-vous que le modèle Profile existe
    try:
        profile = request.user.profile
        if not profile.is_teacher():
            messages.error(request, "Accès réservé aux enseignants.")
            return redirect('flower_detector:home')
    except AttributeError:
        # Si le profil n'existe pas
        messages.error(request, "Profil enseignant non trouvé.")
        return redirect('flower_detector:home')
    
    # Récupérer tous les parcours de l'enseignant
    paths = LearningPath.objects.filter(teacher=request.user).order_by('-created_at')
    
    # Récupérer les ClassGroup de l'enseignant (pas Class)
    try:
        classes = ClassGroup.objects.filter(teacher=request.user)
        first_class = classes.first() if classes.exists() else None
    except Exception as e:
        # Gestion d'erreur
        classes = []
        first_class = None
        print(f"Erreur lors de la récupération des classes: {e}")
    
    # Statistiques par parcours
    paths_with_stats = []
    for path in paths:
        paths_with_stats.append({
            'path': path,
            'students_count': path.get_enrolled_students_count(),
            'completion_rate': path.get_completion_rate(),
            'flowers_count': path.get_flowers_count(),
        })
    
    context = {
        'paths': paths_with_stats,
        'first_class': first_class,
        'classes': classes,
    }
    
    return render(request, 'flower_detector/learning_paths_list.html', context)

@login_required
def create_learning_path(request):
    """Créer un nouveau parcours d'apprentissage"""
    profile = request.user.profile
    
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        difficulty = request.POST.get('difficulty', 'beginner')
        learning_objectives = request.POST.get('learning_objectives', '')
        estimated_duration = request.POST.get('estimated_duration', 30)
        points_reward = request.POST.get('points_reward', 100)
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Récupérer les fleurs sélectionnées
        flowers = request.POST.getlist('flowers')
        
        # Classes sélectionnées
        class_groups_ids = request.POST.getlist('class_groups')
        
        if not title or not flowers:
            messages.error(request, "Le titre et au moins une fleur sont requis.")
            return redirect('flower_detector:create_learning_path')
        
        # Créer le parcours
        path = LearningPath.objects.create(
            teacher=request.user,
            title=title,
            description=description,
            difficulty=difficulty,
            learning_objectives=learning_objectives,
            flowers_sequence=flowers,
            estimated_duration=int(estimated_duration),
            points_reward=int(points_reward),
            start_date=start_date if start_date else None,
            end_date=end_date if end_date else None,
            status='active'  # Actif par défaut
        )
        
        # Assigner aux classes
        if class_groups_ids:
            path.class_groups.set(class_groups_ids)
        
        messages.success(request, f"Parcours '{title}' créé avec succès !")
        return redirect('flower_detector:learning_path_detail', path_id=path.id)
    
    # GET request
    # Récupérer les classes de l'enseignant
    classes = ClassGroup.objects.filter(teacher=request.user)
    
    # Liste des fleurs disponibles
    available_flowers = FlowerInfo.objects.all().values('name', 'scientific_name')
    
    context = {
        'classes': classes,
        'available_flowers': available_flowers,
        'difficulties': LearningPath.DIFFICULTY_CHOICES,
    }
    
    return render(request, 'flower_detector/create_learning_path.html', context)


@login_required
def learning_path_detail(request, path_id):
    """Détails d'un parcours d'apprentissage"""
    profile = request.user.profile
    
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    path = get_object_or_404(LearningPath, id=path_id, teacher=request.user)
    
    # Statistiques
    total_enrolled = path.get_enrolled_students_count()
    completion_rate = path.get_completion_rate()
    
    # Progression des étudiants
    progress_records = PathProgress.objects.filter(path=path).select_related('student')
    
    # Grouper par statut
    completed_students = progress_records.filter(is_completed=True)
    in_progress_students = progress_records.filter(is_completed=False)
    
    context = {
        'path': path,
        'total_enrolled': total_enrolled,
        'completion_rate': completion_rate,
        'completed_students': completed_students,
        'in_progress_students': in_progress_students,
    }
    
    return render(request, 'flower_detector/learning_path_detail.html', context)


@login_required
def edit_learning_path(request, path_id):
    """Modifier un parcours existant"""
    profile = request.user.profile
    
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    path = get_object_or_404(LearningPath, id=path_id, teacher=request.user)
    
    if request.method == 'POST':
        path.title = request.POST.get('title')
        path.description = request.POST.get('description')
        path.difficulty = request.POST.get('difficulty')
        path.learning_objectives = request.POST.get('learning_objectives', '')
        path.estimated_duration = int(request.POST.get('estimated_duration', 30))
        path.points_reward = int(request.POST.get('points_reward', 100))
        path.start_date = request.POST.get('start_date') or None
        path.end_date = request.POST.get('end_date') or None
        path.status = request.POST.get('status', 'active')
        
        # Mettre à jour les fleurs
        flowers = request.POST.getlist('flowers')
        if flowers:
            path.flowers_sequence = flowers
        
        # Mettre à jour les classes
        class_groups_ids = request.POST.getlist('class_groups')
        path.class_groups.set(class_groups_ids)
        
        path.save()
        
        messages.success(request, "Parcours mis à jour avec succès !")
        return redirect('flower_detector:learning_path_detail', path_id=path.id)
    
    # GET request
    classes = ClassGroup.objects.filter(teacher=request.user)
    available_flowers = FlowerInfo.objects.all().values('name', 'scientific_name')
    
    context = {
        'path': path,
        'classes': classes,
        'available_flowers': available_flowers,
        'difficulties': LearningPath.DIFFICULTY_CHOICES,
    }
    
    return render(request, 'flower_detector/edit_learning_path.html', context)


@login_required
def delete_learning_path(request, path_id):
    """Supprimer un parcours"""
    profile = request.user.profile
    
    if not profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    path = get_object_or_404(LearningPath, id=path_id, teacher=request.user)
    
    if request.method == 'POST':
        path_title = path.title
        path.delete()
        messages.success(request, f"Parcours '{path_title}' supprimé avec succès.")
        return redirect('flower_detector:learning_paths_list')
    
    context = {'path': path}
    return render(request, 'flower_detector/delete_learning_path_confirm.html', context)


# ==========================================
# VUES SÉQUENCES PÉDAGOGIQUES - ÉTUDIANT
# ==========================================

@login_required
def student_learning_paths(request):
    """Liste des parcours disponibles pour l'étudiant"""
    profile = request.user.profile
    
    if not profile.is_student():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('flower_detector:home')
    
    # Récupérer les classes de l'étudiant
    my_classes = request.user.student_classes.all()
    
    # Parcours disponibles pour ces classes
    available_paths = LearningPath.objects.filter(
        class_groups__in=my_classes,
        status='active'
    ).distinct()
    
    # Ajouter les informations de progression
    paths_with_progress = []
    for path in available_paths:
        try:
            progress = PathProgress.objects.get(student=request.user, path=path)
        except PathProgress.DoesNotExist:
            progress = None
        
        paths_with_progress.append({
            'path': path,
            'progress': progress,
            'is_available': path.is_available(),
        })
    
    context = {
        'paths_with_progress': paths_with_progress,
    }
    
    return render(request, 'flower_detector/student_learning_paths.html', context)


@login_required
def start_learning_path(request, path_id):
    """Démarrer un parcours d'apprentissage"""
    profile = request.user.profile
    
    if not profile.is_student():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('flower_detector:home')
    
    path = get_object_or_404(LearningPath, id=path_id)
    
    # Vérifier que l'étudiant a accès à ce parcours
    my_classes = request.user.student_classes.all()
    if not path.class_groups.filter(id__in=my_classes.values_list('id', flat=True)).exists():
        messages.error(request, "Vous n'avez pas accès à ce parcours.")
        return redirect('flower_detector:student_learning_paths')
    
    # Vérifier si disponible
    if not path.is_available():
        messages.error(request, "Ce parcours n'est pas encore disponible ou est expiré.")
        return redirect('flower_detector:student_learning_paths')
    
    # Créer ou récupérer la progression
    progress, created = PathProgress.objects.get_or_create(
        student=request.user,
        path=path
    )
    
    if created:
        messages.success(request, f"Parcours '{path.title}' démarré ! Bonne chance ! 🌸")
    else:
        messages.info(request, f"Reprise du parcours '{path.title}'")
    
    return redirect('flower_detector:learning_path_progress', path_id=path.id)


@login_required
def learning_path_progress(request, path_id):
    """Vue de progression d'un parcours pour l'étudiant"""
    profile = request.user.profile
    
    if not profile.is_student():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('flower_detector:home')
    
    path = get_object_or_404(LearningPath, id=path_id)
    
    # Récupérer la progression
    try:
        progress = PathProgress.objects.get(student=request.user, path=path)
    except PathProgress.DoesNotExist:
        messages.error(request, "Vous devez d'abord démarrer ce parcours.")
        return redirect('flower_detector:start_learning_path', path_id=path.id)
    
    # Prochaine fleur à identifier
    next_flower = progress.get_next_flower()
    remaining_flowers = progress.get_remaining_flowers()
    
    # Informations sur la fleur actuelle
    flower_info = None
    if next_flower:
        try:
            flower_info = FlowerInfo.objects.get(name=next_flower.lower())
        except FlowerInfo.DoesNotExist:
            pass
    
    context = {
        'path': path,
        'progress': progress,
        'next_flower': next_flower,
        'remaining_flowers': remaining_flowers,
        'flower_info': flower_info,
    }
    
    return render(request, 'flower_detector/learning_path_progress.html', context)

@login_required
def student_learning_paths(request):
    """Liste des parcours disponibles pour l'étudiant - VERSION CORRIGÉE"""
    profile = request.user.profile
    
    if not profile.is_student():
        messages.error(request, "Accès réservé aux étudiants.")
        return redirect('flower_detector:home')
    
    # Récupérer les classes de l'étudiant
    my_classes = request.user.student_classes.all()
    
    # 🔧 CORRECTION 1 : Vérifier si l'étudiant est dans des classes
    if not my_classes.exists():
        messages.warning(request, "Vous n'êtes inscrit dans aucune classe. Rejoignez une classe pour accéder aux parcours !")
        context = {
            'paths_with_progress': [],
            'no_classes': True,  # Flag pour afficher un message spécial
        }
        return render(request, 'flower_detector/student_learning_paths.html', context)
    
    # 🔧 CORRECTION 2 : Récupérer les parcours disponibles
    # Filtrer par classes ET statut actif
    available_paths = LearningPath.objects.filter(
        class_groups__in=my_classes,
        status='active'
    ).distinct().order_by('-created_at')
    
    # 🔧 CORRECTION 3 : Debug - Afficher les informations
    print(f"DEBUG - Étudiant: {request.user.username}")
    print(f"DEBUG - Classes: {[c.name for c in my_classes]}")
    print(f"DEBUG - Parcours trouvés: {available_paths.count()}")
    for path in available_paths:
        print(f"  - {path.title} (Classes: {[c.name for c in path.class_groups.all()]})")
    
    # Ajouter les informations de progression
    paths_with_progress = []
    for path in available_paths:
        try:
            progress = PathProgress.objects.get(student=request.user, path=path)
        except PathProgress.DoesNotExist:
            progress = None
        
        paths_with_progress.append({
            'path': path,
            'progress': progress,
            'is_available': path.is_available(),
        })
    
    context = {
        'paths_with_progress': paths_with_progress,
        'my_classes': my_classes,  # Ajouté pour debug
        'no_classes': False,
    }
    
    return render(request, 'flower_detector/student_learning_paths.html', context)


# 🔧 AJOUT : Vue de débogage pour l'enseignant
@login_required
def debug_learning_paths(request):
    """Vue de débogage pour vérifier les parcours et assignations"""
    if not request.user.profile.is_teacher():
        messages.error(request, "Accès réservé aux enseignants.")
        return redirect('flower_detector:home')
    
    paths = LearningPath.objects.filter(teacher=request.user)
    
    debug_info = []
    for path in paths:
        info = {
            'title': path.title,
            'status': path.status,
            'classes_assigned': list(path.class_groups.values_list('name', flat=True)),
            'students_with_access': [],
        }
        
        # Trouver tous les étudiants qui ont accès
        for class_group in path.class_groups.all():
            students = class_group.students.all()
            for student in students:
                info['students_with_access'].append(student.username)
        
        debug_info.append(info)
    
    return JsonResponse({'paths': debug_info}, json_dumps_params={'indent': 2})
# ==========================================
# MODIFICATION DE LA VUE PREDICT
# ==========================================

# Modifiez votre vue predict existante pour intégrer les parcours
@login_required
def predict(request):
    if request.method == 'POST':
        form = FlowerImageForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                image_file = request.FILES['image']

                media_dir = os.path.join(settings.MEDIA_ROOT, 'uploaded_images')
                os.makedirs(media_dir, exist_ok=True)

                timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{timestamp}_{image_file.name}"
                image_path = os.path.join(media_dir, filename)

                with open(image_path, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)

                predictor = get_predictor()
                result = predictor.predict(image_path)

                prediction = FlowerPrediction.objects.create(
                    user=request.user,
                    image=f'uploaded_images/{filename}',
                    predicted_class=result['predicted_class'],
                    confidence=result['confidence'],
                    description=result['description'],
                    note='Mode modèle (ResNet50)'
                )

                # 🆕 Vérifier si l'utilisateur est dans un parcours actif
                if hasattr(request.user, 'profile') and request.user.profile.is_student():
                    active_progress = PathProgress.objects.filter(
                        student=request.user,
                        is_completed=False
                    ).first()
                    
                    if active_progress:
                        # Mettre à jour la progression
                        success, message = active_progress.update_progress(
                            result['predicted_class'],
                            result['confidence'],
                            prediction.id
                        )
                        
                        if success:
                            messages.success(request, f"✅ {message}")
                            if active_progress.is_completed:
                                messages.success(request, f"🎉 Félicitations ! Vous avez complété le parcours '{active_progress.path.title}' !")
                        else:
                            messages.warning(request, f"⚠️ {message}")

                messages.success(request, f'Fleur identifiée : {result["predicted_class"].capitalize()}')
                return redirect('flower_detector:result', prediction_id=prediction.id)

            except Exception as e:
                messages.error(request, f"Erreur lors de la prédiction : {str(e)}")

    else:
        form = FlowerImageForm()

    return render(request, 'flower_detector/predict.html', {'form': form})