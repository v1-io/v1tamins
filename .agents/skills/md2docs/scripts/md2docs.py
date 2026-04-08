#!/usr/bin/env python3
"""Convert a Markdown file to a formatted Google Doc and open it in the browser.

Strategy: Convert markdown to styled HTML, then upload via Google Drive API
which natively converts HTML into a Google Doc. This gives us full GFM support
(tables, code blocks, nested lists, etc.) without reimplementing a renderer.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

TOKEN_DIR = Path.home() / ".md2docs"
TOKEN_PATH = TOKEN_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def ensure_dependencies():
    """Install required packages if missing."""
    missing = []
    try:
        import markdown  # noqa: F401
    except ImportError:
        missing.append("markdown")
    try:
        import google.oauth2.credentials  # noqa: F401
        import google_auth_oauthlib.flow  # noqa: F401
        import googleapiclient.discovery  # noqa: F401
    except ImportError:
        missing.extend(["google-auth", "google-auth-oauthlib", "google-api-python-client"])

    if missing:
        print(f"Installing: {', '.join(missing)}...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )


def find_client_secret():
    """Locate client_secret.json in known locations."""
    candidates = [
        Path.home() / ".md2docs" / "client_secret.json",
        Path.home() / ".config" / "md2docs" / "client_secret.json",
    ]
    env_path = os.environ.get("MD2DOCS_CLIENT_SECRET")
    if env_path:
        candidates.insert(0, Path(env_path))

    for p in candidates:
        if p.exists():
            return p
    return None


def authenticate():
    """Authenticate with Google OAuth2 and return credentials."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        client_secret = find_client_secret()
        if not client_secret:
            print("ERROR: No client_secret.json found.")
            print()
            print("Setup instructions:")
            print("  1. Go to https://console.cloud.google.com/apis/credentials")
            print("  2. Create an OAuth 2.0 Client ID (Desktop app)")
            print("  3. Download the JSON and save it to: ~/.md2docs/client_secret.json")
            print()
            print("  Or set MD2DOCS_CLIENT_SECRET=/path/to/client_secret.json")
            sys.exit(1)

        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret), SCOPES)
        creds = flow.run_local_server(port=0)

    TOKEN_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN_PATH.write_text(creds.to_json())
    return creds


# Minimal CSS - let Google Docs use its own native heading/paragraph styles.
# Only style things Docs doesn't handle well natively.
GFM_STYLE = """
<style>
  a { color: #0366d6; }
</style>
"""


def render_mermaid_blocks(md_text):
    """Find ```mermaid blocks, render them to PNG via mmdc, and replace with
    base64-embedded <img> tags wrapped in a marker so they survive markdown conversion.

    Returns (modified_md_text, list_of_image_html_strings).
    Falls back to a regular code block if mmdc is not available.
    """
    import base64
    import shutil

    mmdc = shutil.which("mmdc")
    npx = shutil.which("npx")
    if not mmdc and not npx:
        return md_text, []

    images = []
    counter = [0]

    def replace_mermaid(m):
        mermaid_source = m.group(1)
        idx = counter[0]
        counter[0] += 1

        try:
            # Write mermaid source to temp file
            mmd_file = os.path.join(tempfile.gettempdir(), f"md2docs_mermaid_{idx}.mmd")
            png_file = os.path.join(tempfile.gettempdir(), f"md2docs_mermaid_{idx}.png")
            with open(mmd_file, "w") as f:
                f.write(mermaid_source)

            # Try global mmdc first, fall back to npx
            rendered = False
            if mmdc:
                result = subprocess.run(
                    [mmdc, "-i", mmd_file, "-o", png_file, "-b", "white", "-s", "2"],
                    capture_output=True, timeout=30,
                )
                rendered = result.returncode == 0
            if not rendered and npx:
                subprocess.run(
                    [npx, "--yes", "@mermaid-js/mermaid-cli",
                     "-i", mmd_file, "-o", png_file, "-b", "white", "-s", "2"],
                    capture_output=True, timeout=60,
                )

            if os.path.exists(png_file):
                with open(png_file, "rb") as f:
                    b64 = base64.b64encode(f.read()).decode()
                os.unlink(mmd_file)
                os.unlink(png_file)
                img_html = f'<img src="data:image/png;base64,{b64}" style="max-width:100%">'
                images.append(img_html)
                # Use a placeholder that won't be mangled by markdown
                return f"\n\nMERMAID_IMAGE_{idx}\n\n"
        except Exception:
            pass

        # Fallback: render as regular code block
        return m.group(0).replace("```mermaid", "```")

    md_text = re.sub(
        r"```mermaid\s*\n(.*?)```",
        replace_mermaid,
        md_text,
        flags=re.DOTALL,
    )

    return md_text, images


def inject_mermaid_images(html, images):
    """Replace MERMAID_IMAGE_N placeholders with actual <img> tags."""
    for i, img_html in enumerate(images):
        html = html.replace(f"MERMAID_IMAGE_{i}", img_html)
        # Also catch it wrapped in <p> tags
        html = html.replace(f"<p>MERMAID_IMAGE_{i}</p>", img_html)
    return html


def preprocess_markdown(md_text):
    """Fix common GFM constructs that Python markdown doesn't handle.

    - Ensure blank line before tables (Python markdown requires it, GFM doesn't)
    - Ensure blank line before lists (both * and - markers)
    - Convert any list indentation to 4-space (Python markdown requires 4)
    """
    lines = md_text.split("\n")
    result = []

    # Pattern to match list items and capture their indentation
    list_pattern = re.compile(r"^(\s*)([-*]|\d+\.)\s+(.*)$")

    def is_list_item(line):
        return list_pattern.match(line) is not None

    def is_table_row(line):
        return re.match(r"^\|.+\|$", line.strip()) is not None

    # First pass: detect the indent unit used in the document
    indent_unit = 4  # default
    indents = []
    for line in lines:
        match = list_pattern.match(line)
        if match and match.group(1):
            indents.append(len(match.group(1)))
    if indents:
        # Find the smallest non-zero indent (the base unit)
        min_indent = min(indents)
        if min_indent > 0:
            indent_unit = min_indent

    def normalize_list_indent(line):
        """Convert indentation to 4-space based on detected indent unit."""
        match = list_pattern.match(line)
        if not match:
            return line
        indent = match.group(1)
        marker = match.group(2)
        content = match.group(3)
        if indent:
            spaces = len(indent)
            # Calculate nesting level based on detected indent unit
            level = spaces // indent_unit
            new_indent = "    " * level
            return f"{new_indent}{marker} {content}"
        return line

    for i, line in enumerate(lines):
        prev_line = lines[i - 1] if i > 0 else ""
        prev_stripped = prev_line.strip()

        # Insert blank line before tables if needed
        if (is_table_row(line)
                and i > 0
                and prev_stripped != ""
                and not is_table_row(prev_line)):
            result.append("")

        # Insert blank line before lists if needed
        # Only if previous line is not blank, not a list item, and not a heading
        if (is_list_item(line)
                and i > 0
                and prev_stripped != ""
                and not is_list_item(prev_line)
                and not prev_stripped.startswith("#")):
            result.append("")

        # Normalize list indentation
        if is_list_item(line):
            line = normalize_list_indent(line)

        result.append(line)
    return "\n".join(result)


def postprocess_html(html):
    """Add inline styles for elements that Google Docs HTML import needs.

    Google Docs reliably handles inline styles but ignores most <style> CSS.
    """
    # Code blocks: convert each line inside <pre><code> into a separate <p> inside
    # a single-cell borderless table. Google Docs respects background-color and
    # font-family on <td>, and preserves <p> line breaks inside table cells.
    def format_code_block(m):
        inner = m.group(1)
        # Strip <code> wrapper if present
        inner = re.sub(r"</?code[^>]*>", "", inner)
        # Decode HTML entities for display
        inner = inner.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        inner = inner.replace("&quot;", '"')
        # Convert each line to a styled paragraph
        lines = inner.split("\n")
        # Remove trailing empty line that fenced_code often adds
        if lines and lines[-1].strip() == "":
            lines = lines[:-1]
        styled_lines = []
        for line in lines:
            # Re-encode for HTML
            safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            # Use non-breaking spaces to preserve leading whitespace
            if safe.startswith(" "):
                leading = len(safe) - len(safe.lstrip(" "))
                safe = "\u00a0" * leading + safe.lstrip(" ")
            if safe == "":
                safe = "\u00a0"  # Empty lines need content to render
            styled_lines.append(
                f'<p style="font-family:Courier New;'
                f"font-size:11pt;margin:0;line-height:1.0\">{safe}</p>"
            )
        cell_content = "".join(styled_lines)
        return (
            '<table style="width:100%;border-collapse:collapse;margin:6pt 0">'
            "<tr>"
            '<td style="background-color:#f0f0f0;border:1px solid #d0d0d0;padding:8pt 12pt">'
            f"{cell_content}"
            "</td></tr></table>"
        )

    html = re.sub(r"<pre>(.*?)</pre>", format_code_block, html, flags=re.DOTALL)

    # Inline code: Google Docs needs background-color:#f0f0f0 and
    # font-family:Courier New (unquoted, no fallback list) on a <span>.
    html = re.sub(
        r"<code>(.*?)</code>",
        r'<span style="background-color:#f0f0f0;font-family:Courier New;font-size:11pt">\1</span>',
        html,
    )

    # Data tables: compact styling with borders.
    # Convert <thead>/<th> to regular <tr>/<td> with bold styling so Google Docs
    # doesn't treat the header as a repeating row across page breaks.
    html = re.sub(r"</?t(head|body)>", "", html)
    html = re.sub(
        r"<th>",
        '<td style="border:1px solid #dfe2e5;padding:3pt 8pt;background-color:#f6f8fa;font-weight:bold">',
        html,
    )
    html = re.sub(r"</th>", "</td>", html)
    html = re.sub(
        r"<table>",
        '<table style="border-collapse:collapse;width:100%;margin:4pt 0">',
        html,
    )
    html = re.sub(
        r"<td>",
        '<td style="border:1px solid #dfe2e5;padding:3pt 8pt">',
        html,
    )

    # Google Docs collapses spacing around table elements (both data tables
    # and our code-block tables). Add a spacer paragraph after every </table>
    # so content that follows always has breathing room.
    html = re.sub(
        r"(</table>)\s*(?!<p><br>)",
        r"\1<p><br></p>",
        html,
    )

    # Add vertical spacing to list items for better readability
    # Use line-height and padding since Google Docs may ignore margin on <li>
    html = re.sub(
        r"<li>",
        '<li style="line-height:1.5;padding-bottom:2pt">',
        html,
    )

    # Add space before lists (between paragraph text and first bullet)
    html = re.sub(
        r"<(ul|ol)>",
        r'<\1 style="margin-top:8pt">',
        html,
    )

    return html


def markdown_to_html(md_text, title):
    """Convert markdown text to a styled HTML document."""
    import markdown

    # Render mermaid blocks to images before markdown conversion
    md_text, mermaid_images = render_mermaid_blocks(md_text)
    md_text = preprocess_markdown(md_text)

    extensions = [
        "markdown.extensions.tables",
        "markdown.extensions.fenced_code",
        "markdown.extensions.toc",
        "markdown.extensions.sane_lists",
        "markdown.extensions.smarty",
    ]

    html_body = markdown.markdown(md_text, extensions=extensions)
    html_body = postprocess_html(html_body)
    html_body = inject_mermaid_images(html_body, mermaid_images)

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  {GFM_STYLE}
</head>
<body>
{html_body}
</body>
</html>"""


def upload_html_as_doc(creds, title, html_content):
    """Upload HTML to Google Drive, converting to a Google Doc. Returns the doc URL."""
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    drive_service = build("drive", "v3", credentials=creds)

    # Write HTML to a temp file for upload
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html_content)
        tmp_path = f.name

    try:
        file_metadata = {
            "name": title,
            "mimeType": "application/vnd.google-apps.document",  # Convert to Google Doc
        }
        media = MediaFileUpload(tmp_path, mimetype="text/html", resumable=True)
        doc = drive_service.files().create(
            body=file_metadata, media_body=media, fields="id,webViewLink"
        ).execute()
    finally:
        os.unlink(tmp_path)

    return doc.get("webViewLink", f"https://docs.google.com/document/d/{doc['id']}/edit")


def main():
    parser = argparse.ArgumentParser(description="Convert Markdown to a formatted Google Doc")
    parser.add_argument("file", help="Path to the markdown file")
    parser.add_argument("--title", help="Google Doc title (default: filename without extension)")
    parser.add_argument("--no-open", action="store_true", help="Don't open the doc in browser")
    args = parser.parse_args()

    md_path = Path(args.file)
    if not md_path.exists():
        print(f"ERROR: File not found: {md_path}")
        sys.exit(1)

    title = args.title or md_path.stem.replace("-", " ").replace("_", " ").title()
    md_text = md_path.read_text(encoding="utf-8")

    ensure_dependencies()

    print("Authenticating with Google...")
    creds = authenticate()

    print("Converting markdown to HTML...")
    html = markdown_to_html(md_text, title)

    print(f"Creating Google Doc: {title}")
    doc_url = upload_html_as_doc(creds, title, html)

    print(f"Doc created: {doc_url}")

    if not args.no_open:
        print("Opening in browser...")
        webbrowser.open(doc_url)

    print(f"\n{doc_url}")


if __name__ == "__main__":
    main()
