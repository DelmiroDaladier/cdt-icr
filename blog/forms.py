from django import forms
from .models import BlogPost, Author, Category

class BlogPostForm(forms.ModelForm):

    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    text = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}))
    authors = forms.ModelMultipleChoiceField(
                    queryset=Author.objects.all(),
                    widget = forms.SelectMultiple(attrs={'class': 'form-control'}))

    categories = authors = forms.ModelMultipleChoiceField(
                    queryset=Category.objects.all(),
                    widget = forms.SelectMultiple(attrs={'class': 'form-control'}))

    class Meta:
        model = BlogPost
        fields = ['title',
                  'text',
                  'authors',
                  'categories']

        labels = {'title': 'Title',
                  'text' : 'Body',
                  'authors': 'Authors',
                  'categories': 'Categories' }