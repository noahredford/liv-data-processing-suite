from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('brycer_processor/', views.brycer_processor, name='brycer_processor'),
    path('data_scrubber/', views.data_scrubber, name='data_scrubber'),
    path('kml_to_business/', views.kml_to_business, name='kml_to_business'),
]