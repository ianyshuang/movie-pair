from django.urls import path
from . import views

urlpatterns = [
  path('top/', views.top, name = 'top'),
  path('category/', views.category, name = 'category'),
  path('submit/<str:movie_id>', views.submit, name = 'submit'),
  path('<str:movie_id>/', views.detail, name= 'detail'),
  path('form/<str:movie_id>', views.form, name = 'form')
]