from django.contrib import admin
from .models import Image, Evaluator, Classifier
# Register your models here.

admin.site.register(Image)
admin.site.register(Evaluator)
admin.site.register(Classifier)