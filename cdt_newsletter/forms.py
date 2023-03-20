from django import forms
from .models import Subscription, Newsletter

class Subscriptionform(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = Subscription
        fields = ['email']
        labels = ['Email']

class Newsletterform(forms.ModelForm):
    class Meta:
        model = Newsletter
        fields = '__all__'