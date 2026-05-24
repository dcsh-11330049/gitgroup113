from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.index, name='login'),
    
    # Dashboard Views
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),
    path('dashboard/president/', views.president_dashboard, name='president_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Authentication APIs
    path('api/login/', views.api_login, name='api_login'),
    path('api/logout/', views.api_logout, name='api_logout'),
    path('api/current-user/', views.api_current_user, name='api_current_user'),
    
    # Club APIs
    path('api/clubs/', views.clubs_api, name='clubs_api'),
    path('api/my-clubs/', views.api_my_clubs, name='api_my_clubs'),
    path('api/clubs/<int:club_id>/', views.api_club_detail, name='api_club_detail'),
    path('api/clubs/<int:club_id>/documents/', views.api_club_documents, name='api_club_documents'),
    path('api/clubs/<int:club_id>/members/', views.api_club_members, name='api_club_members'),
    
    # Club Description Modification APIs
    path('api/clubs/<int:club_id>/submit-modification/', views.api_submit_description_modification, name='api_submit_modification'),
    path('api/clubs/<int:club_id>/pending-modifications/', views.api_pending_modifications, name='api_pending_modifications'),
    path('api/modifications/<int:modification_id>/approve/', views.api_approve_modification, name='api_approve_modification'),
    path('api/modifications/<int:modification_id>/reject/', views.api_reject_modification, name='api_reject_modification'),
    
    # System Settings APIs
    path('api/system-settings/', views.api_system_settings, name='api_system_settings'),
    path('api/system-settings/update/', views.api_update_system_settings, name='api_update_system_settings'),
    
    # Transfer Logs API
    path('api/transfers/submit/', views.api_submit_transfer_application, name='api_submit_transfer'),
    path('api/transfers/mine/', views.api_my_transfer_applications, name='api_my_transfers'),
    path('api/transfers/pending/', views.api_pending_transfer_applications, name='api_pending_transfers'),
    path('api/transfers/<int:application_id>/review/', views.api_review_transfer_application, name='api_review_transfer'),
    path('api/transfer-logs/', views.api_transfer_logs, name='api_transfer_logs'),
]
