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

from html import unescape
from django.utils.html import strip_tags

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
        queryset=Announcement.objects.none(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "form-control",
                "id": "id_announcements",
            }
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['announcements'].queryset = Announcement.objects.filter(
            published=False
        )

        self.fields['announcements'].label_from_instance = (
            lambda obj: unescape(strip_tags(obj.title)).strip()
        )

    class Meta:
        model = Newsletter
        fields = ['title', 'text', 'announcements']


class DateInput(forms.DateInput):
    input_type = "date"


class AnnouncementForm(forms.ModelForm):
    title = forms.CharField(
        widget=TinyMCE(attrs={'cols': 80, 'rows': 10, "height": 200}, 
        mce_attrs={
            'height': 200,
            'toolbar':  "undo redo | formatselect | "
            "bold italic underline forecolor backcolor | "
            }))

    text = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 30}))
    
    date = forms.DateField(
        required=False,
        widget=DateInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Announcement
        fields = ["title", "text"]
