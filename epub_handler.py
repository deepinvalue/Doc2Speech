import zipfile
from bs4 import BeautifulSoup

def list_html_files(epub_path):
    """
    List the HTML files contained in the EPUB (ZIP) file.
    """
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        all_files = zip_ref.namelist()
        html_files = [f for f in all_files if f.endswith('html')]
    return html_files

def extract_html_content(epub_path, file_name):
    """
    Extract and return the content of a specified HTML file from the EPUB (ZIP) archive.
    """
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        with zip_ref.open(file_name) as f:
            return f.read()
