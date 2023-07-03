from django import forms
from .models import Subscription, Newsletter, Announcement
from repository.models import Conference

class Subscriptionform(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = Subscription
        fields = ['email']
        labels = ['Email']

class Newsletterform(forms.ModelForm):

    title = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'})
    )

    tldr = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control'
            }
        )
    )

    text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control'
            }
        )
    )    

    announcements = forms.ModelMultipleChoiceField(
        queryset=Announcement.objects.filter(published=False),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Newsletter
        fields = ['title', 'tldr', 'text']

class AnnouncementForm(forms.ModelForm):

    title = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'form-control'})
    )

    text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control'
            }
        )
    )

    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
                'class': 'form-control'
            })
    )

    class Meta:
        model = Announcement
        fields = ['title', 'text']