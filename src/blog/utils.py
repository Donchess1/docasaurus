import markdown
from rest_framework import serializers


def parse_markdown_file(markdown_file):
    try:
        markdown_content = markdown_file.read().decode("utf-8")
        html_content = markdown.markdown(markdown_content)
        return html_content
    except Exception as e:
        raise serializers.ValidationError(
            "Error occurred parsing markdown file: {}".format(str(e))
        )
