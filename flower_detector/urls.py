from django.urls import path
from . import views
from .views import (
    home,
    register_view,
    login_view,
    logout_view,
    predict,
    history,
    result,
    chat_api,
    dashboard,
    analytics_api,
    global_analytics,
    export_analytics_pdf,
    teacher_dashboard,
    teacher_classes,
    create_class,
    class_detail,
    student_detail,
    student_dashboard,
    join_class,
    # Add the new views for learning paths
    learning_paths_list,
    create_learning_path,
    learning_path_detail,
    edit_learning_path,
    delete_learning_path,
    student_learning_paths,
    start_learning_path,
    learning_path_progress,
  
)
from . import reporting_views

app_name = "flower_detector"

urlpatterns = [
    # ... existing URLs ...
    path("", views.home, name="home"),
    path("predict/", views.predict, name="predict"),
    path("history/", views.history, name="history"),
    path("result/<int:prediction_id>/", views.result, name="result"),

    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    path("api/chat/", views.chat_api, name="chat_api"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/analytics/', views.analytics_api, name='analytics_api'),
    path('dashboard/global/', views.global_analytics, name='global_analytics'),
    path('dashboard/export-pdf/', views.export_analytics_pdf, name='export_pdf'),
    
    # TEACHER/STUDENT ROUTES
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/classes/', teacher_classes, name='teacher_classes'),
    path('teacher/student/<int:student_id>/', views.student_detail, name='student_detail'),
    path('teacher/class/create/', views.create_class, name='create_class'),
    path('teacher/class/<int:class_id>/', views.class_detail, name='class_detail'),
    
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/join-class/', views.join_class, name='join_class'),
    
    # ==========================================
    # LEARNING PATHS - TEACHER
    # ==========================================
    path('teacher/learning-paths/', learning_paths_list, name='learning_paths_list'),
    path('teacher/learning-paths/create/', create_learning_path, name='create_learning_path'),
    path('teacher/learning-paths/<int:path_id>/', learning_path_detail, name='learning_path_detail'),
    path('teacher/learning-paths/<int:path_id>/edit/', edit_learning_path, name='edit_learning_path'),
    path('teacher/learning-paths/<int:path_id>/delete/', delete_learning_path, name='delete_learning_path'),
    
    # ==========================================
    # LEARNING PATHS - STUDENT
    # ==========================================
    path('student/learning-paths/', student_learning_paths, name='student_learning_paths'),
    path('student/learning-paths/<int:path_id>/start/', start_learning_path, name='start_learning_path'),
    path('student/learning-paths/<int:path_id>/progress/', learning_path_progress, name='learning_path_progress'),
        

        # Rapports PDF par étudiant
    path('teacher/student-report/<int:student_id>/',
         reporting_views.student_report_pdf,
         name='student_report_pdf'),
    
    # Rapport PDF par classe
    path('teacher/class-report/<int:class_id>/',
         reporting_views.class_report_pdf,
         name='class_report_pdf'),
    
    # Rapport hebdomadaire par email (les deux noms pour compatibilité)
    path('teacher/send-weekly-report/',
         reporting_views.send_weekly_report,
         name='send_weekly_report'),
    
    path('teacher/generate-weekly-report/',
         reporting_views.send_weekly_report,
         name='generate_weekly_report'),
    
    # Classement des étudiants
    path('teacher/student-ranking/',
         reporting_views.student_ranking,
         name='student_ranking'),
    
    # Identification des difficultés
    path('teacher/difficult-flowers/',
         reporting_views.difficult_flowers_report,
         name='difficult_flowers_report'),
    
    # Export Excel (les deux noms pour compatibilité)
    path('teacher/export-excel/',
         reporting_views.export_excel,
         name='export_excel'),
    
    path('teacher/export-all-data/',
         reporting_views.export_excel,
         name='export_all_data'),
    
    # Rapport mensuel PDF
    path('teacher/monthly-report/',
         reporting_views.monthly_report_pdf,
         name='monthly_report_pdf'),
path('offline/', views.offline_view, name='offline'),
 # Recommandations
    path('recommendations/', views.recommendations_view, name='recommendations'),
    path('recommendations/api/', views.recommendations_api, name='recommendations_api'),
    path('recommendations/click/<int:recommendation_id>/', views.recommendation_click, name='recommendation_click'),
    path('recommendations/refresh/', views.refresh_recommendations, name='refresh_recommendations'),
]

