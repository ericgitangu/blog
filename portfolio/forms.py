from django import forms

from .models import Comments

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ('name', 'email', 'comment')
        labels = {
            'name': 'Name 🧑',
            'email': 'Email Address 📥 ',
            'comment': 'Drop your comment here 👇',
            }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'comment': forms.Textarea(attrs={'class': 'form-control'}),
            }
        errors = {
            'name': {'required': 'Please enter your name',
                     'min_length': 'Please enter your name with at least 6 characters'},
            'email': {'required': 'Please enter a valid email address'},
            'comment': {'required': 'Please enter your comment with at least 10 characters',
                        'min_length': 'Please enter your comment with at least 10 characters'},
            }