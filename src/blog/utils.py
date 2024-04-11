import markdown
from rest_framework import serializers

def parse_markdown_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
            html_content = markdown.markdown(markdown_content)
            return html_content
    except Exception as e:
        raise serializers.ValidationError("Error occurred parsing markdown file: {}".format(str(e)))
