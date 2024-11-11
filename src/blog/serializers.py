from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from .models import BlogPost, Tag
from .utils import parse_markdown_file


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class BlogPostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.name")
    reading_time = serializers.ReadOnlyField()
    is_draft = serializers.BooleanField(default=False)
    markdown_file = serializers.FileField(write_only=True, required=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = BlogPost
        fields = [
            "tags",
            "id",
            "title",
            "content",
            "tags",
            "reading_time",
            "cover_image_url",
            "author",
            "markdown_file",
            "deleted_at",
            "is_archived",
            "published_at",
            "is_draft",
            "created_at",
            "updated_at",
        ]

    @transaction.atomic
    def create(self, validated_data):
        markdown_file = validated_data.pop("markdown_file", None)
        markdown_content = markdown_file.read().decode("utf-8")
        validated_data["content"] = markdown_content
        is_draft = validated_data.get("is_draft", False)
        if not is_draft:
            validated_data["published_at"] = timezone.now()

        tags_data = self.context.get("tags", [])
        blog_post = super().create(validated_data)

        blog_post.tags.set(tags_data)
        blog_post.save()
        return blog_post

    @transaction.atomic
    def update(self, instance, validated_data):
        markdown_file = validated_data.pop("markdown_file", None)
        if markdown_file:
            markdown_content = markdown_file.read().decode("utf-8")
            validated_data["content"] = markdown_content
        instance = super().update(instance, validated_data)
        tags = self.context.get("tags", None)
        if tags is not None:
            instance.tags.set(tags)
        return instance
