from celery import shared_task
from .models import Evaluator, Image, Classifier
import requests
from .serializers import ImageSerializer, EvaluatorSerializer, ClassifierSerializer
from io import BytesIO
from PIL import Image as PILImage
import tensorflow as tf
from rest_framework.response import Response
import time
import boto3    
import numpy as np
from django.conf import settings
import os
@shared_task
def test_images_creator(pages, data):
    i=0
    print("Running shared task")
    for page in pages:
        for obj in page['Contents']:
            if obj['Key'].endswith('.jpg') or obj['Key'].endswith('.jpeg') or obj['Key'].endswith('.png'):
                print('Created img file '+str(i), end='\r')
                if data['label'] == "Image":
                    image = Image(name=f"{data['label']}_{obj['Key']}", 
                              img=f"https://agricloudbucket.s3.eu-central-1.amazonaws.com/{obj['Key']}")
                else:
                    image = Evaluator(name=obj['Key'], 
                                    img=f"https://agricloudbucket.s3.eu-central-1.amazonaws.com/{obj['Key']}",
                                    label=data['label'])
                image.save()
                i+=1
    return 0
@shared_task
def evaluate_script( data, images):
    preprocessed_new_images=[]
    i=0
    for image in images:
        if i>10:
            break
        print('Started img file '+str(i), end='\r')
        serializer = EvaluatorSerializer(image, many = False) 
        response = requests.get(serializer['img'].value)
        img = PILImage.open(BytesIO(response.content))
        # Preprocess the image
        img = img.resize((224, 224))
        img = np.array(img)
        img = img / 255.0
        # Convert the image to a TensorFlow tensor
        img = tf.keras.preprocessing.image.img_to_array(img)
        img = tf.expand_dims(img, 0)
        preprocessed_new_images.append(img)
        i+=1
    new_labels = np.zeros(i)
    images = Evaluator.objects.filter(label=Evaluator.NOT_LANTERNFLY_LABEL)
    i=0
    print("\n")
    preprocessed_new_images2=[]
    for image in images:
        if i>10:
            break
        print('Started img file '+str(i), end='\r')
        serializer = EvaluatorSerializer(image, many = False) 
        response = requests.get(serializer['img'].value)
        img = PILImage.open(BytesIO(response.content))
        # Preprocess the image
        img = img.resize((224, 224))
        img = np.array(img)
        img = img / 255.0
        # Convert the image to a TensorFlow tensor
        img = tf.keras.preprocessing.image.img_to_array(img)
        img = tf.expand_dims(img, 0)
        preprocessed_new_images2.append(img)
        i+=1
    new_labels2 = np.full(i,1)
    preprocessed_new_images3 = preprocessed_new_images+preprocessed_new_images2
    new_labels3=np.concatenate((new_labels,new_labels2))
    new_labels3=new_labels3.reshape((-1,1))
    if data['last'] == 'False':
        last_classifier = Classifier.objects.get(name = data['model'])
    else:
        if Classifier.objects.exists():
            last_classifier = Classifier.objects.last()
        else:
            last_classifier = Classifier(name="my_model4.h5", new_images_number=0)
    print("\n")
    print(f"Loading the model {last_classifier.name}...", end='\r')
    s3 = boto3.client('s3',
                        aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
                        aws_secret_access_key= settings.AWS_S3_SECRET_ACCESS_KEY)
    s3.download_file(settings.AWS_STORAGE_BUCKET_NAME, f"models/{last_classifier.name}", f"{last_classifier.name}")
    model = tf.keras.models.load_model(f"{last_classifier.name}")
    print("\n")
    print("Compiling the model...", end='\r')
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
        loss=tf.keras.losses.BinaryCrossentropy(),
        metrics=['accuracy']
    )
    #print(model.summary())
    # Stack the tensors together to form a batch
    batch_tensor = tf.stack(preprocessed_new_images3, axis=0)
    test_data = tf.data.Dataset.from_tensor_slices((batch_tensor, new_labels3))
    print("\n")
    print("Evaluating the model...", end='\r')
    print("\n")
    result = model.evaluate(test_data)
    print("Test Loss:", result[0])
    print("Test Accuracy:", result[1])
    last_classifier.test_loss = result[0]
    last_classifier.test_accuracy = result[1]
    last_classifier.save()
    os.remove(f"{last_classifier.name}")

@shared_task
def retrain_script( data, images):
    RETRAIN_LIMIT = 100
    i=0
    preprocessed_new_images=[]
    for image in images:
        print('Started img file '+str(i), end='\r')
        if(i>=RETRAIN_LIMIT):
            break
        serializer = ImageSerializer(image, many = False) 
        #print("IMAGEEE:", serializer['img'].value)
        response = requests.get(serializer['img'].value)
        img = PILImage.open(BytesIO(response.content))
        # Preprocess the image
        img = img.resize((224, 224))
        img = np.array(img)
        img = img / 255.0

        # Convert the image to a TensorFlow tensor
        img = tf.keras.preprocessing.image.img_to_array(img)
        img = tf.expand_dims(img, 0)
        preprocessed_new_images.append(img)
        i+=1
        image.label = Image.LANTERNFLY_LABEL
        image.save()
    new_labels = np.zeros(i).reshape((-1,1))
    last_number_of_images=0
    if data['last'] == 'False':
        last_classifier = Classifier.objects.get(name = data['model'])
    else:
        if Classifier.objects.exists():
            last_classifier = Classifier.objects.last()
        else:
            last_classifier= Classifier.objects.create(name="my_model4.h5", new_images_number = 0)
    print("\n")
    print("Loading the model...", end='\r')
    s3 = boto3.client('s3',
                        aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
                        aws_secret_access_key= settings.AWS_S3_SECRET_ACCESS_KEY)
    obj = s3.get_object(Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=f"models/{last_classifier.name}")
    in_memory = BytesIO(obj['Body'].read())
    model = tf.keras.models.load_model(in_memory)
    print("\n")
    print("Compiling the model...", end='\r')
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
        loss=tf.keras.losses.BinaryCrossentropy(),
        metrics=['accuracy']
    )
    print(model.summary())
    batch_tensor = tf.stack(preprocessed_new_images, axis=0)
    train_data = tf.data.Dataset.from_tensor_slices((batch_tensor, new_labels))
    print("\n")
    print("Training the model...", end='\r')
    model.fit(train_data)
    new_model_name="model_"+str(round(time.time()))+".h5"
    new_classifier = Classifier.objects.create(name=new_model_name, new_images_number = last_number_of_images)
    in_memory = BytesIO()
    print("\n")
    print("Saving the model...", end='\r')
    model.save(in_memory, format='h5')
    in_memory.seek(0)
    
    s3.upload_fileobj(in_memory,settings.AWS_STORAGE_BUCKET_NAME, f"models/{new_model_name}")