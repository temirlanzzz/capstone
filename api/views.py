from django.shortcuts import render
import tensorflow as tf
from PIL import Image as PILImage
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import Image, Evaluator, Classifier
from .serializers import ImageSerializer, EvaluatorSerializer, ClassifierSerializer
from rest_framework import serializers
import time
import boto3    
from django.core.files.base import ContentFile
import requests
from io import BytesIO
import numpy as np
from django.conf import settings
from . import tasks
# Initialise environment variables
#create all image instances from aws bucket

@api_view(['POST'])
def create_images(request):
    print("Creating test images")
    s3 = boto3.client('s3',
                        aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
                        aws_secret_access_key= settings.AWS_S3_SECRET_ACCESS_KEY)
    data = request.data
    prefix=data['prefix']#'test/n101/'
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Prefix=prefix)
    try:    
        tasks.test_images_creator(pages=pages, data=data).apply_async()
        return Response(status=status.HTTP_401_UNAUTHORIZED)
    except:
        return Response(status=status.HTTP_200_OK) 

    
    
#create image 
    
@api_view(['DELETE'])
def deleteAllImages(request):
    data = request.data
    if data['all']=="True":
        image = Image.objects.all().delete()
    else:
        image = Image.objects.filter(label = data["label"]).delete()
    return Response('images were deleted.')

@api_view(['DELETE'])
def deleteAllEvaluators(request):
    data = request.data
    if data['all']=="True":
        image = Evaluator.objects.all().delete()
    else:
        image = Evaluator.objects.filter(label = data["label"]).delete()
    return Response('test images of lanternfly were deleted.')

@api_view(['DELETE'])
def deleteAllClassifiers(request):
    classifier = Classifier.objects.all().delete()
    return Response('classifiers were deleted.')

@api_view(['POST'])
def create_image(request):
    data = request.data
    image = Image.objects.create(
        img = data['img'],
        name = data['name'],
        label = Image.NOT_LABELED,
        status = Image.NOT_USED_STATUS,
        date_labeled = str(time.time())
    )
    serializer = ImageSerializer(image, many = False)
    return Response(serializer.data)

@api_view(['POST'])
def change_label(request):
    image = Image.objects.get(id=request.data['id'])
    image.label = request.data['label']
    image.status = Image.USED_STATUS
    image.save()
    if(Image.objects.filter(status=Image.USED_STATUS).count() >100):
        response = retrain_model()
    serializer = ImageSerializer(image, many = False)
    return Response(serializer.data)
#shows single image on mobile app
@api_view(['GET'])
def get_image(request, pk):
    image = Image.objects.get(id=pk)
    serializer = ImageSerializer(image, many = False)
    return Response(serializer.data)
#shows single image on mobile app
@api_view(['GET'])
def get_evaluator(request, pk):
    image = Evaluator.objects.get(id=pk)
    serializer = EvaluatorSerializer(image, many = False)
    return Response(serializer.data)
#shows single unlabeled image on mobile app
@api_view(['GET'])
def get_unlabeled_image(request):
    image = Image.objects.filter(label=Image.NOT_LABELED)[0]
    serializer = ImageSerializer(image, many = False)
    return Response(serializer.data)
@api_view(['GET'])
def get_number_used(request):
    images = Image.objects.filter(status=Image.USED_STATUS).count()
    return Response({"message": "Mobile app used images number:"+str(images)}, status=status.HTTP_200_OK)
@api_view(['GET'])
def get_test_zero_number(request):
    images = Evaluator.objects.filter(label=Evaluator.LANTERNFLY_LABEL).count()
    return Response({"message": "Lanterfly test number:"+str(images)}, status=status.HTTP_200_OK)
@api_view(['GET'])
def get_test_one_number(request):
    images = Evaluator.objects.filter(label=Evaluator.NOT_LANTERNFLY_LABEL).count()
    return Response({"message": "Not Lanterfly test number:"+str(images)}, status=status.HTTP_200_OK)
@api_view(['GET'])
def revert(request): 
    response = ""
    unlabel = unlabel_labeled(request="")
    if(unlabel.status_code==200):
        response += "Unlabeled. "
    unused = unused_used()
    if(unused.status_code==200):
        response += "Unused. "
    deleteclassifiers =deleteAllClassifiers()
    if(deleteclassifiers.status_code == 200):
        response+= "Deleted all classifiers. "
    return Response({"message":response}, status=status.HTTP_200_OK)
@api_view(['POST'])
def evaluate_model(request):
    print("loading test images")
    data = request.data
    tasks.evaluate_script.apply_async(args=(data), queue='queue_name')
    return Response({"message": f"Model tested successfully"}, status=status.HTTP_200_OK)
    

@api_view(['GET'])
def get_classifier(request,pk):
    classifier = Classifier.objects.get(id=pk)
    serializer = ClassifierSerializer(classifier, many=False)
    return Response(serializer.data)

@api_view(['GET'])
def get_classifiers(request):
    classifier = Classifier.objects.all() 
    serializer = ClassifierSerializer(classifier, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def unlabel_labeled(request):
    images = Image.objects.filter(label=Image.LANTERNFLY_LABEL)
    for image in images:
        image.label = Image.NOT_LABELED
        image.save()
    return Response({"message": "Number of images unlabeled:"+str(images)}, status=status.HTTP_200_OK)
@api_view(['GET'])
def unused_used(request):
    images = Image.objects.filter(status=Image.USED_STATUS)
    for image in images:
        image.status = Image.NOT_USED_STATUS
        image.save()
    return Response({"message": "Number of images status changed to unused:"+str(images)}, status=status.HTTP_200_OK)

@api_view(['POST'])
def retrain_model(request):
    print("Retraining the model...")
    data = request.data
    tasks.retrain_script.apply_async(args = (data), queue='queue_name')
    return Response({"message": "Model retrained successfully."}, status=status.HTTP_200_OK)
        


#shows all images
@api_view(['GET'])
def get_images(request):
    image = Image.objects.all()
    serializer = ImageSerializer(image, many = True, context={"request": request})
    return Response(serializer.data)

#shows all test images
@api_view(['GET'])
def get_evaluators(request):
    image = Evaluator.objects.all()
    serializer = EvaluatorSerializer(image, many = True, context={"request": request})
    return Response(serializer.data)

#upload single image
@api_view(['POST'])
def upload_image(request):
    data = request.data

@api_view(['GET'])
def getRoutes(request):
    routes = [
        {
            'Endpoint' : '/notes/',
            'method' : 'GET',
            'body' : None,
            'description' : 'Returns an array of notes',
        },
    ]
    return Response(routes)

