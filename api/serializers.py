from .models import Image, Evaluator, Classifier
from rest_framework import serializers

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('id','name','img','label','status','date_labeled')
class EvaluatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluator
        fields = ('id','name','img','label')
class ClassifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Classifier
        fields = ('id','name','date_created','new_images_number', 'test_loss', 'test_accuracy')
        