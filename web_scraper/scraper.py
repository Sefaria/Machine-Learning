from pathlib import Path

import hashlib, re, os
from readability import Document

from time import sleep
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

BASE_DIR = Path(__file__).resolve(strict=True).parent


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


def parse_html(html):
    # create soup object
    soup = BeautifulSoup(html, "html.parser")
    output_list = []
    # parse soup object to get wikipedia article url, title, and last modified date
    article_url = soup.find("link", {"rel": "canonical"})["href"]
    article_title = soup.find("h1", {"id": "firstHeading"}).text
    article_last_modified = soup.find("li", {"id": "footer-info-lastmod"}).text
    article_info = {
        "url": article_url,
        "title": article_title,
        "last_modified": article_last_modified,
    }
    output_list.append(article_info)
    return output_list


def get_load_time(article_url):
    try:
        # set headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
        }
        # make get request to article_url
        response = requests.get(
            article_url, headers=headers, stream=True, timeout=3.000
        )
        # get page load time
        load_time = response.elapsed.total_seconds()
    except Exception as e:
        print(e)
        load_time = "Loading Error"
    return load_time


def get_text_to_save(url, html):
    doc = Document(html)
    text = re.sub(r"<[^>]+>", "", doc.summary(html_partial=True))
    return f"{url}\n{doc.title()}\n{text}"  # add url to top line of file


def get_filename(url):
    hash_filename = hashlib.md5(url.encode()).hexdigest()
    return Path(BASE_DIR).joinpath(f"output/{hash_filename}.txt")


def write_to_file(url, text):
    with open(get_filename(url), "w") as fout:
        fout.write(text)
