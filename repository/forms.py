from django import forms
from django.contrib.admin import widgets
from django.contrib.auth.models import (
    User,
)
from django.contrib.auth.forms import (
    UserCreationForm,
)

from .models import (
    Publication,
    Author,
    Venue,
    ResearchArea,
    Conference,
    Session,
)


class DateInput(forms.DateInput):
    input_type = "date"


class PublicationForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        )
    )
    overview = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control"}
        )
    )
    authors = forms.ModelMultipleChoiceField(
        help_text="Click in the box to access "
        "the Authors List, or add a new one.",
        queryset=Author.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "multi-select-form form-control"
            }
        ),
    )
    research_area = forms.ModelMultipleChoiceField(
        help_text="Click in the box to access the "
        "Reasearh Area List, or add a new one.",
        queryset=ResearchArea.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "multi-select-form form-control"
            }
        ),
    )
    venue = forms.ModelMultipleChoiceField(
        help_text="Click in the box to access"
        " the Venue List, or add a new one.",
        required=False,
        queryset=Venue.objects.all(),
        widget=forms.SelectMultiple(
            attrs={
                "class": "multi-select-form form-control"
            }
        ),
    )
    citation = forms.URLField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )
    pdf = forms.URLField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )
    supplement = forms.URLField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )
    slides = forms.URLField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )
    poster = forms.URLField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )
    code = forms.URLField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )
    video = forms.URLField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    class Meta:
        model = Publication
        fields = [
            "name",
            "overview",
            "authors",
            "thumbnail",
            "research_area",
            "venue",
            "citation",
            "pdf",
            "supplement",
            "slides",
            "poster",
            "code",
            "video",
        ]

        labels = {
            "name": "Title",
            "overview": "TLDR",
            "authors": "Authors",
            "thumbnail": "Image",
            "research_area": "Research Area",
            "venue": "Venue",
            "citation": "Citation",
            "pdf": "Pdf Link",
            "supplement": "Supplement",
            "slides": "Slides",
            "poster": "Poster",
            "code": "Code",
            "video": "Video",
        }


class AuthorForm(forms.ModelForm):
    class Meta:
        model = Author
        fields = ["user_name", "user_url"]
        labels = ["name", "url"]


class VenueForm(forms.ModelForm):
    class Meta:
        model = Venue
        fields = [
            "venue_name",
            "venue_url",
        ]
        labels = ["Name", "URL"]


class ResearchAreaForm(forms.ModelForm):
    class Meta:
        model = ResearchArea
        fields = ["title"]
        labels = ["Title"]


class ArxivForm(forms.Form):
    link = forms.CharField(max_length=200)


class NewUserForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control"}
        ),
    )

    short_bio = forms.CharField(
        required=True,
        widget=forms.Textarea(
            attrs={"class": "form-control"}
        ),
    )

    username = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={"class": "form-control"}
        ),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password",
        )

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class ConferenceForm(forms.ModelForm):
    date_formats = [
        "%Y-%m-%d",  # '2006-10-25'
        "%m/%d/%Y",  # '10/25/2006'
        "%m/%d/%y",  # '10/25/06'
        "%b %d %Y",  # 'Oct 25 2006'
        "%b %d, %Y",  # 'Oct 25, 2006'
        "%d %b %Y",  # '25 Oct 2006'
        "%d %b, %Y",  # '25 Oct, 2006'
        "%B %d %Y",  # 'October 25 2006'
        "%B %d, %Y",  # 'October 25, 2006'
        "%d %B %Y",  # '25 October 2006'
        "%d %B, %Y",  # '25 October, 2006'
        "%d %b",
        "%d %B",
    ]

    venue_url = forms.CharField(
        help_text="Conference URL.",
        max_length=200,
        widget=forms.TextInput(
            attrs={"class": "conference_link form-control"}
        ),
    )

    venue_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    start_date = forms.DateField(
        required=False,
        input_formats=date_formats,
        widget=DateInput(attrs={"class": "form-control"}),
    )
    end_date = forms.DateField(
        required=False,
        input_formats=date_formats,
        widget=DateInput(attrs={"class": "form-control"}),
    )
    location = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control"}
        ),
    )

    class Meta:
        model = Conference
        fields = [
            "venue_url",
            "venue_name",
            "start_date",
            "end_date",
            "location",
        ]
        labels = {
            "venue_name": "Name",
            "venue_url": "Conference Link",
            "location": "Location",
            "start_date": "Starting on",
            "end_date": "To",
        }


class SessionForm(forms.ModelForm):
    SESSION_CHOICES = (
        ("WORKSHOP", "Workshop"),
        ("TUTORIAL", "Tutorial"),
    )

    PUBLICATION_CHOICES = (
        ("PAPER", "Paper"),
        ("BOOK", "Book"),
        ("PROCEEDINGS", "Proceedings"),
    )

    start_date = forms.DateField(
        required=True,
        widget=DateInput(attrs={"class": "form-control"}),
    )

    end_date = forms.DateField(
        required=True,
        widget=DateInput(attrs={"class": "form-control"}),
    )

    type = forms.ChoiceField(
        required=True,
        choices=SESSION_CHOICES,
        widget=forms.Select(
            attrs={"class": "form-control"}
        ),
    )

    conference = forms.ModelChoiceField(
        queryset=Conference.objects.all(),
        required=False,
        widget=forms.Select(
            attrs={"class": "form-control"}
        ),
    )

    class Meta:
        model = Session
        fields = [
            "start_date",
            "end_date",
            "type",
            "conference",
        ]
