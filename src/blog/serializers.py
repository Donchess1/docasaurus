from django.db import transaction
from rest_framework import serializers
from .models import *
from .utils import parse_markdown_file

class BlogPostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source="author.name")
    reading_time = serializers.ReadOnlyField()
    markdown_file = serializers.FileField(write_only=True, required=True)
    cover_image = serializers.ImageField()

    class Meta:
        model = BlogPost
        fields = ["tags","id","title","content","reading_time", "cover_image_url", "author", "markdown_file",
                  "created_at", "updated_at", "deleted_at", "is_archived","is_draft", "cover_image"]
        
    
    @transaction.atomic
    def create(self, validated_data):
        markdown_file = validated_data.pop("markdown_file")
        # html_content = parse_markdown_file(markdown_file)
        # validated_data["content"] = html_content
        markdown_content = markdown_file.read().decode("utf-8")
        validated_data["content"] = markdown_content
        cover_image = validated_data.get("cover_image")
        obj = self.upload_client.execute(cover_image, "MYBALANCE/COVER_IMAGE")
        cover_image_url = obj["data"]["url"]
        

        post= BlogPost.objects.create(**validated_data)
        post.is_draft = True
        post.save()
        return post

    @transaction.atomic
    def update(self, instance, validated_data):
        markdown_file = validated_data.pop("markdown_file", None)
        if markdown_file:
            # html_content = parse_markdown_file(markdown_file)
            # validated_data["content"] = html_content
            markdown_content = markdown_file.read().decode("utf-8")
            validated_data["content"] = markdown_content
        instance = super().update(instance, validated_data)
        tags = validated_data.get("tags", None)
        if tags is not None:
            instance.tags = tags
        return instance