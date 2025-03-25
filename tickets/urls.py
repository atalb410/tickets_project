from django.urls import path
from . import views

urlpatterns = [
    # Home and Login URLs
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='custom_login'),
    path('logout/', views.custom_logout, name='custom_logout'),
    
    # Dashboard URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('engineer-dashboard/', views.engineer_dashboard, name='engineer_dashboard'),
    path('agent-dashboard/', views.agent_dashboard, name='agent_dashboard'),
    
    # Request URLs
    path('raise-quotation/', views.raise_quotation_request, name='raise_quotation_request'),
    path('assign-request/<int:request_id>/', views.assign_request, name='assign_request'),
    path('resolve-request/<int:request_id>/', views.resolve_request, name='resolve_request'),
    path('mark-incomplete/<int:request_id>/', views.mark_incomplete, name='mark_incomplete'),
    path('edit-request/<int:request_id>/', views.edit_request, name='edit_request'),
    path('view-request/<int:request_id>/', views.view_request, name='view_request'),
    path('accept-quote/<int:request_id>/<int:quote_id>/', views.accept_quote, name='accept_quote'),
    path('reject-quote/<int:request_id>/<int:quote_id>/', views.reject_quote, name='reject_quote'),
    path('request-payment-link/<int:request_id>/', views.request_payment_link, name='request_payment_link'),
    path('request/<int:quotation_request_id>/quote/<int:quote_id>/change/', views.request_quote_change, name='request_quote_change'),
    path('request/quote/change/ajax/', views.request_quote_change_ajax, name='request_quote_change_ajax'),
    path('request-inspection/<int:request_id>/', views.request_inspection, name='request_inspection'),
    path('quotation_request/<int:quotation_request_id>/add_comment/', views.add_comment, name='add_comment'),
]