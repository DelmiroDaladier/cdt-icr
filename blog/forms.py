from django import forms
from .models import BlogPost, Author, ResearchArea


class BlogPostForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    text = forms.CharField(widget=forms.Textarea(attrs={"class": "form-control"}))

    class Meta:
        model = BlogPost
        fields = ["name", "text"]

        labels = {"name": "Title", "text": "Body"}
