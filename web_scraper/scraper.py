from pathlib import Path

import hashlib, re, os
from readability import Document
from util.spacy_registry import create_language_detector
import spacy

from time import sleep
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

BASE_DIR = Path(__file__).resolve(strict=True).parent
spacy.prefer_gpu()
nlp = spacy.load('en_core_web_sm')
nlp.add_pipe('language_detector', last=True)


def get_driver(headless):
    options = webdriver.ChromeOptions()
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


def get_text_to_save(url, html):
    if len(html) == 0: return ""
    doc = Document(html)
    text = re.sub(r"<[^>]+>", "", doc.summary(html_partial=True))
    if len(text) == 0: return ""
    lang = detect_language(text)
    return f"{url}\n{doc.title()}\n{lang['language']} {lang['score']:{1}.{2}}\n{text}"  # add url to top line of file


def get_filename(url):
    hash_filename = hashlib.md5(url.encode()).hexdigest()
    return Path(BASE_DIR).joinpath(f"output/{hash_filename}.txt")


def write_to_file(filename, text):
    with open(filename, "w") as fout:
        fout.write(text)


def detect_language(text):
    doc = nlp(text)
    return doc._.language
