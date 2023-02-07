from django.db import models

# Create your models here.

class Image(models.Model):
    LANTERNFLY_LABEL = 0
    NOT_LANTERNFLY_LABEL = 1
    NOT_LABELED = 2
    LABEL_CHOICES = (
        (LANTERNFLY_LABEL, 'Lanternfly'),
        (NOT_LANTERNFLY_LABEL, 'Not Lanternfly'),
        (NOT_LABELED, 'Not Labeled')
    )
    NOT_USED_STATUS = 1
    USED_STATUS = 2
    STATUS_CHOICES = (
        (NOT_USED_STATUS, 'Not used in app'),
        (USED_STATUS, 'Was labeled in app'),
    )
    name = models.CharField(max_length=200)
    img = models.TextField()
    label = models.IntegerField(choices=LABEL_CHOICES, default=NOT_LABELED)
    status = models.IntegerField(choices=STATUS_CHOICES, default=NOT_USED_STATUS)
    date_labeled = models.DateField(auto_now_add=True, blank=True)

class Evaluator(models.Model):
    LANTERNFLY_LABEL = 0
    NOT_LANTERNFLY_LABEL = 1
    NOT_LABELED = 2
    LABEL_CHOICES = (
        (LANTERNFLY_LABEL, 'Lanternfly'),
        (NOT_LANTERNFLY_LABEL, 'Not Lanternfly'),
        (NOT_LABELED, 'Not Labeled')
    )
    name = models.CharField(max_length=200)
    img = models.TextField()
    label = models.IntegerField(choices=LABEL_CHOICES, default=NOT_LABELED)

class Classifier(models.Model):
    name = models.CharField(max_length=200)
    new_images_number = models.IntegerField()
    date_created = models.DateField(auto_now_add=True, blank=True)
    test_loss = models.FloatField(default=-1.0)
    test_accuracy = models.FloatField(default=-1.0)
