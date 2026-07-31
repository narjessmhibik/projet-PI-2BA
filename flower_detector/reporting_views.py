# reporting_views.py - VERSION FINALE CORRIGÉE
# Compatible avec votre structure de modèles (student_classes au lieu de class_groups)

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
import io

from .models import UserProfile, FlowerPrediction, ClassGroup
from django.contrib.auth.models import User


@login_required
def student_report_pdf(request, student_id):
    """Génère un rapport PDF détaillé pour un étudiant"""
    
    if request.user.profile.role != 'teacher':
        return redirect('flower_detector:home')
    
    student = get_object_or_404(User, id=student_id)
    
    # Utiliser student_classes au lieu de class_groups
    if not student.student_classes.filter(teacher=request.user).exists():
        return HttpResponse("Acces refuse", status=403)
    
    predictions = FlowerPrediction.objects.filter(user=student).order_by('-created_at')
    total_predictions = predictions.count()
    
    avg_confidence = predictions.aggregate(Avg('confidence'))['confidence__avg'] or 0
    success_predictions = predictions.filter(confidence__gte=80).count()
    success_rate = (success_predictions / total_predictions * 100) if total_predictions > 0 else 0
    
    top_flowers = predictions.values('predicted_class').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    elements.append(Paragraph("Rapport d'Etudiant", title_style))
    elements.append(Paragraph(f"{student.username}", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Informations Generales", heading_style))
    
    # Utiliser student_classes.all()
    classes_list = ', '.join([c.name for c in student.student_classes.all()])
    
    info_data = [
        ['Nom d\'utilisateur', student.username],
        ['Email', student.email],
        ['Date d\'inscription', student.date_joined.strftime('%d/%m/%Y')],
        ['Classe(s)', classes_list or 'Aucune']
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Statistiques Principales", heading_style))
    
    stats_data = [
        ['Nombre total d\'analyses', str(total_predictions)],
        ['Confiance moyenne', f"{avg_confidence:.1f}%"],
        ['Taux de reussite', f"{success_rate:.1f}%"],
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#667eea')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 20))
    
    if top_flowers:
        elements.append(Paragraph("Top 5 Fleurs Identifiees", heading_style))
        
        flowers_data = [['Fleur', 'Nombre']]
        for flower in top_flowers:
            flowers_data.append([flower['predicted_class'].capitalize(), str(flower['count'])])
        
        flowers_table = Table(flowers_data, colWidths=[4*inch, 2*inch])
        flowers_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        elements.append(flowers_table)
        elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Dernieres Analyses (10 recentes)", heading_style))
    
    recent_data = [['Date', 'Fleur', 'Confiance']]
    for pred in predictions[:10]:
        recent_data.append([
            pred.created_at.strftime('%d/%m/%Y %H:%M'),
            pred.predicted_class.capitalize(),
            f"{pred.confidence:.1f}%"
        ])
    
    recent_table = Table(recent_data, colWidths=[2*inch, 2.5*inch, 1.5*inch])
    recent_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elements.append(recent_table)
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        f"Genere le {timezone.now().strftime('%d/%m/%Y a %H:%M')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_{student.username}_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


@login_required
def class_report_pdf(request, class_id):
    """Génère un rapport comparatif PDF pour une classe"""
    
    if request.user.profile.role != 'teacher':
        return redirect('flower_detector:home')
    
    class_group = get_object_or_404(ClassGroup, id=class_id, teacher=request.user)
    students = class_group.students.all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    elements.append(Paragraph("Rapport de Classe", title_style))
    elements.append(Paragraph(f"{class_group.name}", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Informations de la Classe", heading_style))
    
    class_info = [
        ['Nom de la classe', class_group.name],
        ['Code', class_group.code],
        ['Enseignant', request.user.username],
        ['Nombre d\'etudiants', str(students.count())],
        ['Date de creation', class_group.created_at.strftime('%d/%m/%Y')]
    ]
    
    class_table = Table(class_info, colWidths=[2.5*inch, 3.5*inch])
    class_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elements.append(class_table)
    elements.append(Spacer(1, 20))
    
    elements.append(Paragraph("Comparaison des Etudiants", heading_style))
    
    comparison_data = [['Rang', 'Etudiant', 'Analyses', 'Confiance Moy.', 'Taux Reussite']]
    
    student_stats = []
    for student in students:
        predictions = FlowerPrediction.objects.filter(user=student)
        total = predictions.count()
        avg_conf = predictions.aggregate(Avg('confidence'))['confidence__avg'] or 0
        success = predictions.filter(confidence__gte=80).count()
        success_rate = (success / total * 100) if total > 0 else 0
        
        student_stats.append({
            'student': student,
            'total': total,
            'avg_conf': avg_conf,
            'success_rate': success_rate
        })
    
    student_stats.sort(key=lambda x: x['total'], reverse=True)
    
    for i, stat in enumerate(student_stats, 1):
        comparison_data.append([
            str(i),
            stat['student'].username,
            str(stat['total']),
            f"{stat['avg_conf']:.1f}%",
            f"{stat['success_rate']:.1f}%"
        ])
    
    comparison_table = Table(comparison_data, colWidths=[0.8*inch, 2*inch, 1.2*inch, 1.5*inch, 1.5*inch])
    comparison_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elements.append(comparison_table)
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        f"Genere le {timezone.now().strftime('%d/%m/%Y a %H:%M')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_classe_{class_group.name}_{timezone.now().strftime("%Y%m%d")}.pdf"'
    
    return response


@login_required
@login_required
def send_weekly_report(request):
    """Envoie un rapport hebdomadaire via SendGrid"""
    
    if request.user.profile.role != 'teacher':
        return JsonResponse({'status': 'error', 'message': 'Accès refusé'})
    
    try:
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        # Utiliser classes au lieu de class_groups
        classes = ClassGroup.objects.filter(teacher=request.user)
        
        # Utiliser student_classes au lieu de class_groups
        total_students = User.objects.filter(student_classes__in=classes).distinct().count()
        total_predictions = FlowerPrediction.objects.filter(
            user__student_classes__in=classes,
            created_at__gte=start_date
        ).distinct().count()
        
        context = {
            'teacher': request.user,
            'start_date': start_date,
            'end_date': end_date,
            'total_students': total_students,
            'total_predictions': total_predictions,
            'classes': classes
        }
        
        html_message = render_to_string('flower_detector/emails/weekly_report.html', context)
        
        send_mail(
            subject=f'Rapport Hebdomadaire - {start_date.strftime("%d/%m/%Y")} au {end_date.strftime("%d/%m/%Y")}',
            message='Votre rapport hebdomadaire est disponible.',
            from_email='noreply@flowerdetector.com',
            recipient_list=[request.user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return JsonResponse({'status': 'success', 'message': 'Rapport envoyé par email !'})
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Erreur: {str(e)}'})
@login_required
def student_ranking(request):
    """Affiche le classement global des étudiants"""
    
    if request.user.profile.role != 'teacher':
        return redirect('flower_detector:home')
    
    classes = ClassGroup.objects.filter(teacher=request.user)
    # Utiliser student_classes au lieu de class_groups
    students = User.objects.filter(student_classes__in=classes).distinct()
    
    student_rankings = []
    for student in students:
        predictions = FlowerPrediction.objects.filter(user=student)
        total = predictions.count()
        avg_conf = predictions.aggregate(Avg('confidence'))['confidence__avg'] or 0
        success = predictions.filter(confidence__gte=80).count()
        success_rate = (success / total * 100) if total > 0 else 0
        
        student_rankings.append({
            'student': student,
            'total_analyses': total,
            'avg_confidence': avg_conf,
            'success_rate': success_rate,
            'last_activity': predictions.first().created_at if predictions.exists() else None
        })
    
    student_rankings.sort(key=lambda x: x['total_analyses'], reverse=True)
    
    context = {'rankings': student_rankings}
    return render(request, 'flower_detector/student_ranking.html', context)


@login_required
def difficult_flowers_report(request):
    """Identifie les fleurs qui posent le plus de difficultés"""
    
    if request.user.profile.role != 'teacher':
        return redirect('flower_detector:home')
    
    classes = ClassGroup.objects.filter(teacher=request.user)
    # Utiliser student_classes au lieu de class_groups
    students = User.objects.filter(student_classes__in=classes).distinct()
    predictions = FlowerPrediction.objects.filter(user__in=students)
    
    flower_stats = predictions.values('predicted_class').annotate(
        total_attempts=Count('id'),
        failed_attempts=Count('id', filter=Q(confidence__lt=60)),
        avg_confidence=Avg('confidence')
    )
    
    difficult_flowers = []
    for flower in flower_stats:
        failure_rate = (flower['failed_attempts'] / flower['total_attempts'] * 100)
        if failure_rate > 20:
            students_struggling = predictions.filter(
                predicted_class=flower['predicted_class'],
                confidence__lt=60
            ).values('user').distinct().count()
            
            difficult_flowers.append({
                'name': flower['predicted_class'],
                'total_attempts': flower['total_attempts'],
                'failed_attempts': flower['failed_attempts'],
                'failure_rate': failure_rate,
                'avg_confidence': flower['avg_confidence'],
                'students_struggling': students_struggling
            })
    
    difficult_flowers.sort(key=lambda x: x['failure_rate'], reverse=True)
    
    context = {'difficult_flowers': difficult_flowers}
    return render(request, 'flower_detector/difficult_flowers.html', context)


@login_required
def export_excel(request):
    """Exporte toutes les données en format Excel"""
    
    if request.user.profile.role != 'teacher':
        return redirect('flower_detector:home')
    
    wb = openpyxl.Workbook()
    
    ws_classes = wb.active
    ws_classes.title = "Classes"
    ws_classes.append(['Nom', 'Code', 'Description', 'Nombre d\'etudiants', 'Date de creation'])
    
    for class_group in ClassGroup.objects.filter(teacher=request.user):
        ws_classes.append([
            class_group.name,
            class_group.code,
            class_group.description,
            class_group.students.count(),
            class_group.created_at.strftime('%d/%m/%Y')
        ])
    
    ws_students = wb.create_sheet("Etudiants")
    ws_students.append(['Nom d\'utilisateur', 'Email', 'Classes', 'Analyses', 'Taux de reussite'])
    
    classes = ClassGroup.objects.filter(teacher=request.user)
    # Utiliser student_classes au lieu de class_groups
    students = User.objects.filter(student_classes__in=classes).distinct()
    
    for student in students:
        predictions = FlowerPrediction.objects.filter(user=student)
        total = predictions.count()
        success = predictions.filter(confidence__gte=80).count()
        success_rate = (success / total * 100) if total > 0 else 0
        
        # Utiliser student_classes.all()
        classes_list = ', '.join([c.name for c in student.student_classes.all()])
        
        ws_students.append([
            student.username,
            student.email,
            classes_list,
            total,
            f"{success_rate:.1f}%"
        ])
    
    ws_predictions = wb.create_sheet("Analyses")
    ws_predictions.append(['Date', 'Etudiant', 'Fleur', 'Confiance', 'Classe'])
    
    for student in students:
        for pred in FlowerPrediction.objects.filter(user=student).order_by('-created_at')[:100]:
            # Utiliser student_classes.all()
            classes_list = ', '.join([c.name for c in student.student_classes.all()])
            
            ws_predictions.append([
                pred.created_at.strftime('%d/%m/%Y %H:%M'),
                student.username,
                pred.predicted_class,
                f"{pred.confidence:.1f}%",
                classes_list
            ])
    
    for ws in [ws_classes, ws_students, ws_predictions]:
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="667eea", end_color="667eea", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="export_donnees_{timezone.now().strftime("%Y%m%d")}.xlsx"'
    
    return response


@login_required
def monthly_report_pdf(request):
    """Génère un rapport PDF pour un mois donné"""
    
    if request.user.profile.role != 'teacher':
        return redirect('flower_detector:home')
    
    month_str = request.GET.get('month')
    
    if not month_str:
        return HttpResponse("Mois non specifie", status=400)
    
    year, month = map(int, month_str.split('-'))
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    classes = ClassGroup.objects.filter(teacher=request.user)
    # Utiliser student_classes au lieu de class_groups
    students = User.objects.filter(student_classes__in=classes).distinct()
    predictions = FlowerPrediction.objects.filter(
        user__in=students,
        created_at__gte=start_date,
        created_at__lt=end_date
    )
    
    total_predictions = predictions.count()
    total_students_active = predictions.values('user').distinct().count()
    avg_confidence = predictions.aggregate(Avg('confidence'))['confidence__avg'] or 0
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    elements.append(Paragraph("Rapport Mensuel", title_style))
    elements.append(Paragraph(f"{start_date.strftime('%B %Y')}", styles['Heading2']))
    elements.append(Spacer(1, 20))
    
    stats_data = [
        ['Total d\'analyses', str(total_predictions)],
        ['Etudiants actifs', str(total_students_active)],
        ['Confiance moyenne', f"{avg_confidence:.1f}%"],
        ['Nombre de classes', str(classes.count())]
    ]
    
    stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 15),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    
    elements.append(stats_table)
    elements.append(Spacer(1, 40))
    elements.append(Paragraph(
        f"Genere le {timezone.now().strftime('%d/%m/%Y a %H:%M')}",
        ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=TA_CENTER)
    ))
    
    doc.build(elements)
    
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="rapport_mensuel_{month_str}.pdf"'
    
    return response