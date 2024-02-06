import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

def read_epub(epub_path):
    """
    Open an EPUB file and return the ebook object.
    """
    try:
        book = epub.read_epub(epub_path)
        return book
    except Exception as e:
        print(f"Failed to read EPUB file: {e}")
        return None

def list_chapters(book):
    """
    List chapters of the EPUB book.
    Returns a list of tuples containing chapter titles and item ids.
    """
    chapters = []
    for item in book.get_items():
        if item.get_name().endswith('html'):
            chapters.append((item.get_name(), item.id))
    return chapters

def extract_chapter_content(book, item_id):
    """
    Extract and return the content of a specified chapter from the EPUB book.
    """
    content = ''
    try:
        item = book.get_item_with_id(item_id)
        content = item.get_content()
    except Exception as e:
        print(f"Failed to extract chapter content: {e}")
    return content
