from rest_framework import serializers

from .models import BlogPost
from .utils import parse_markdown_file

class BlogPostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.name')
    reading_time = serializers.ReadOnlyField()
    markdown_file = serializers.FileField(write_only=True, required=True)
    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "content",
            "reading_time",
            "cover_image_url",
            "author",
            "markdown_file",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        if 'markdown_file' in attrs:
            markdown_file = attrs['markdown_file']
            html_content = parse_markdown_file(markdown_file)
            attrs['content'] = html_content
            print("---->",attrs['content'])
        return attrs

    def create(self, validated_data):
        markdown_file = validated_data.pop('markdown_file')
        html_content = parse_markdown_file(markdown_file)
        validated_data['content'] = html_content
        print("---->", validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        markdown_file = validated_data.pop('markdown_file', None)
        if markdown_file:
            html_content = parse_markdown_file(markdown_file)
            validated_data['content'] = html_content
        return super().update(instance, validated_data)