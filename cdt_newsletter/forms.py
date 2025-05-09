from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import (
    Layout,
    Column,
    Row,
    Fieldset,
)
from .models import (
    Subscription,
    Newsletter,
    Announcement,
)
from tinymce.widgets import TinyMCE
from tinymce import models as tinymce_models
from tinymce.models import HTMLField

class Subscriptionform(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = Subscription
        fields = ["email"]
        labels = ["Email"]


class Newsletterform(forms.ModelForm):
    title = forms.CharField(
        help_text="Newsletter title.",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    tldr = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control"}),
    )

    text = forms.CharField(
        help_text="The text that will appear at the top of the newsletter.",
        required=False,
        widget=TinyMCE(attrs={'cols': 128, 'rows': 10}),
    )

    announcements = forms.ModelMultipleChoiceField(
        help_text="Click in the box to access the Announcement List.",
        queryset=Announcement.objects.filter(published=False),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "announcements-multi-select",
                "multiple": "multiple",
            }
        ),
    )

    class Meta:
        model = Newsletter
        fields = ["title", "tldr", "text"]


class DateInput(forms.DateInput):
    input_type = "date"


class AnnouncementForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))

    text = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))
    
    date = forms.DateField(
        required=False,
        widget=DateInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Announcement
        fields = ["title", "text"]
