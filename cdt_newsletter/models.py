from django.db import models

# Create your models here.
class Subscription(models.Model):
    email = models.EmailField(null=True)
    date = models.DateTimeField(auto_now_add=True)

class Newsletter(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100, null=True)
    text = models.TextField()
    created_at= models.DateField(auto_now_add=True)
    modified_at = models.DateField(auto_now=True)
    sent = models.BooleanField(default=False)

    def __str__(self):
        return self.title
