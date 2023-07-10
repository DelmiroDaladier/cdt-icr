from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Column, Row, Fieldset
from .models import Subscription, Newsletter, Announcement


class Subscriptionform(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = Subscription
        fields = ['email']
        labels = ['Email']


class Newsletterform(forms.ModelForm):

    title = forms.CharField(
        help_text="Newsletter title.",
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
        help_text="The text that will appear at the top of the newsletter.",
        required=False,
        widget=forms.Textarea(
            attrs={
                'class': 'form-control'
            }
        )
    )

    announcements = forms.ModelMultipleChoiceField(
        help_text="Press Ctrl+Click to select the announcements for the newsletter.",
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
        help_text="Add a date to turn this announcement into an event",
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Announcement
        fields = ['title', 'text']