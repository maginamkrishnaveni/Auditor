from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('volunteer/', views.volunteer_select, name='volunteer_select'),
    path('volunteer/change/', views.volunteer_change, name='volunteer_change'),
    path('session/new/', views.session_create, name='session_create'),
    path('session/<int:session_id>/', views.dashboard, name='dashboard'),
    path('session/<int:session_id>/add-book/', views.add_book, name='add_book'),
    path('session/<int:session_id>/book-options/', views.book_options, name='book_options'),
    path('session/<int:session_id>/add-donation/', views.add_donation, name='add_donation'),
    path('session/<int:session_id>/end/', views.end_session, name='end_session'),
    path('session/<int:session_id>/report/', views.report, name='report'),
    path('session/<int:session_id>/export/', views.export_excel, name='export_excel'),
    path('session/<int:session_id>/totals/', views.totals_fragment, name='totals_fragment'),
    path('session/<int:session_id>/recent/', views.recent_fragment, name='recent_fragment'),
]
