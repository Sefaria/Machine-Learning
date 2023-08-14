from pathlib import Path

import hashlib, re, os
from readability import Document
from util.spacy_registry import create_language_detector
import spacy

from time import sleep
import requests
from functools import reduce
from bs4 import BeautifulSoup
from selenium import webdriver

BASE_DIR = Path(__file__).resolve(strict=True).parent
spacy.prefer_gpu()
nlp = spacy.load('en_core_web_sm')
nlp.add_pipe('language_detector', last=True)


def get_driver(headless):
    options = webdriver.ChromeOptions()
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if headless:
        options.add_argument("--headless")
        options.add_argument('--blink-settings=imagesEnabled=false')
        options.add_argument("--disable-javascript")
    # initialize driver
    driver = webdriver.Chrome(chrome_options=options)
    return driver


def connect_to_url(browser, url):
    connection_attempts = 0
    while connection_attempts < 1:
        try:
            browser.get(url)
            sleep(5)
            return True
        except Exception as e:
            connection_attempts += 1
    return False


MANUAL_PARSE_SELECTORS = {
    "929.org.il": {"content": ".content", "title": ".content .title"}
}


def get_text_for_class(soup, class_selector):
    elems = soup.select(class_selector)
    return reduce(lambda a, b: a + b.get_text() + "\n", elems, "")


def get_text_from_html(url, html):
    from urllib.parse import urlparse
    domain = re.sub(r"^www\.", "", urlparse(url).netloc)
    if domain in MANUAL_PARSE_SELECTORS:
        selectors = MANUAL_PARSE_SELECTORS[domain]
        soup = BeautifulSoup(html, 'html.parser')
        content = get_text_for_class(soup, selectors['content'])
        title = get_text_for_class(soup, selectors['title'])
        return title, content

    doc = Document(html)
    content = re.sub(r"<[^>]+>", "", doc.summary(html_partial=False))
    return doc.title(), content


def get_text_to_save(url, html):
    if len(html) == 0: return ""
    title, content = get_text_from_html(url, html)
    if len(content) == 0: return ""
    lang = detect_language(content)
    return f"{url}\n{title}\n{lang['language']} {lang['score']:{1}.{2}}\n{content}"  # add url to top line of file


def get_error_text(url):
    return f"{url}\n$SCRAPING_ERROR$"


def get_filename(url):
    hash_filename = hashlib.md5(url.encode()).hexdigest()
    return Path(BASE_DIR).joinpath(f"output/{hash_filename}.txt")


def write_to_file(filename, text):
    with open(filename, "w") as fout:
        fout.write(text)


def detect_language(text):
    doc = nlp(text)
    return doc._.language
