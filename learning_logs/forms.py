from django import forms
from .models import Topic,Entry,Comment
class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['text','public']
        labels = {'text':'','public':'让所有用户可见'}
class EntryForm(forms.ModelForm):
    class Meta:
        model = Entry
        fields = ['text']
        labels = {'text':''}
        widgets = {'text':forms.Textarea(attrs={'cols':80})}
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text':''}
        widgets = {'text':forms.Textarea(attrs={'rows':3,'placeholder':'写下你的评论...'})}
