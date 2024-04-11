from rest_framework import serializers

from .models import BlogPost


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
            "created_at",
            "updated_at",
        ]
    def validate(self, attrs):
        if 'markdown_file' in attrs:
            markdown_file = attrs['markdown_file']
            html_content = parse_markdown_file(markdown_file)
            attrs['content'] = html_content
        return attrs
