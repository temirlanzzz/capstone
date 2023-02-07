from django.urls import path
from . import views
urlpatterns = [
    path('', views.getRoutes),
    path('retrain/', views.retrain_model),
    path('test/', views.evaluate_model),
    path('randomimage/', views.get_unlabeled_image),
    path('create/', views.create_image),
    path('generate/', views.create_images),
    path('images/', views.get_images),
    path('image/<str:pk>/', views.get_image),
    path('evaluators/', views.get_evaluators),
    path('evaluator/<str:pk>/', views.get_evaluator),
    path('delete/images/', views.deleteAllImages),
    path('delete/evaluators/', views.deleteAllEvaluators),
    path('delete/classifiers/', views.deleteAllClassifiers),
    path('classifier/<str:pk>/', views.get_classifier),
    path('classifiers/', views.get_classifiers),
    path('used/', views.get_number_used),
    path('zeros/', views.get_test_zero_number),
    path('ones/', views.get_test_one_number),
]