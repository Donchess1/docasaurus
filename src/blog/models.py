import math
import uuid
from cloudinary.models import CloudinaryField
from django.db import models
from users.models.user import CustomUser as User





class BlogPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField(null=True, blank=True)
    reading_time = models.PositiveIntegerField(blank=True, null=True)  # in minutes
    cover_image_url = models.URLField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_draft = models.BooleanField(default=True)
    is_archived = models.BooleanField(default=False)
    tags = models.JSONField(default=list)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        words_per_minute = 200  # average reading speed
        total_words = len(self.content.split())
        self.reading_time = math.ceil(total_words / words_per_minute)
        super().save(*args, **kwargs)
