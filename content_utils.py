import re, hashlib, difflib
from bs4 import BeautifulSoup

def clean_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        for tag in soup(['script', 'style', 'svg', 'iframe', 'meta', 'link']):
            tag.decompose()
        for tag in soup.find_all(True):
            if tag.attrs:
                allowed = ['href', 'src', 'alt', 'title']
                tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed}
        clean_text = ' '.join(soup.stripped_strings)
        return re.sub(r'\s+', ' ', clean_text).strip()
    except Exception:
        return html_content

def hash_content(text):
    return hashlib.sha256(text.encode()).hexdigest()

def calculate_similarity(text1, text2):
    if not text1 or not text2:
        return 0.0
    return difflib.SequenceMatcher(None, text1, text2).ratio()