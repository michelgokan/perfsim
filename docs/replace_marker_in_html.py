import os
import re
import sys


def process_html_file(file_path):
    """Reads an HTML file, replaces markers, and writes the changes back to the file."""
    if not os.path.exists(file_path):
        print(f"Error: The file {file_path} does not exist.")
        return

    if not file_path.endswith('.html'):
        print("Error: The specified file is not an HTML file.")
        return

    try:
        with open(file_path, "r", encoding='utf-8') as file:
            html_content = file.read()

        """Replaces markers in HTML content with a very aggressive regex approach."""
        # Attempting to capture div or any container tags surrounding the markers
        html_content = re.sub(
            r'(<blockquote[^>]*>\s*<div[^>]*>\s*<p[^>]*>\s*\[!NOTE\]\s*)(.*?)(\s*</p>\s*</div>\s*</blockquote>)',
            r'<div class="admonition note">\n<p class="admonition-title">Note</p>\n<p>\2</p>\n</div>',
            html_content,
            flags=re.DOTALL | re.IGNORECASE
        )
        html_content = re.sub(
            r'(<blockquote[^>]*>\s*<div[^>]*>\s*<p[^>]*>\s*\[!CAUTION\]\s*)(.*?)(\s*</p>\s*</div>\s*</blockquote>)',
            r'<div class="admonition warning">\n<p class="admonition-title">Warning</p>\n<p>\2</p>\n</div>',
            html_content,
            flags=re.DOTALL | re.IGNORECASE
        )

        with open(file_path, "w", encoding='utf-8') as file:
            file.write(html_content)

        print("The file has been successfully modified.")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <filename>")
    else:
        process_html_file(sys.argv[1])
