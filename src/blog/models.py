import math
import uuid

from django.db import models

from users.models.user import CustomUser as User


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        # Ensure name is stored in uppercase for case-insensitivity
        self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


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
    is_draft = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="blog_posts", blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        words_per_minute = 200  # average reading speed
        total_words = len(self.content.split())
        self.reading_time = math.ceil(total_words / words_per_minute)
        super().save(*args, **kwargs)

    def publish(self):
        self.is_draft = False
        self.published_at = timezone.now()
        self.save()

    def archive(self):
        self.is_archived = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_archived = False
        self.deleted_at = None
        self.save()
