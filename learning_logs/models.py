from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Topic(models.Model):
    text = models.CharField(max_length=200)
    date_added = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User,on_delete=models.CASCADE)
    public =models.BooleanField(default = False)
    def __str__(self):
        return self.text
class Entry(models.Model):
    topic = models.ForeignKey(Topic,on_delete=models.CASCADE)
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "entries"
    
    def __str__(self):
        if len(self.text) <= 50:
            return f"{self.text}"
        else:
            return f"{self.text[:50]}..."
class Comment(models.Model):
    entry = models.ForeignKey(Entry,on_delete=models.CASCADE,related_name='comments')
    owner = models.ForeignKey(User,on_delete=models.CASCADE)
    text = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_added']
    def __str__(self):
        return f"{self.owner.username} 在{self.date_added}的评论"

    