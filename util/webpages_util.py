import dataclasses
import os, re, shutil
from pathlib import Path
from collections import defaultdict
from typing import List, Optional
from iso639 import languages
import math
import tarfile
from util.spacy_registry import create_language_detector
from sefaria.utils.hebrew import strip_cantillation
import spacy
from tqdm import tqdm

DIR = "../web_scraper/output"


@dataclasses.dataclass
class ScrapedWebPage:
    url: str
    title: str
    language: str
    language_confidence: float
    text_lines: List[str]
    filename: str

    def get_text(self):
        return "\n".join(self.text_lines)

    def has_real_data(self) -> bool:
        """
        runs some heuristics to see if this webpage has real data that's worth looking at
        :return:
        """
        BAD_TITLE_STRS = {"502", "Page not found"}
        for bad in BAD_TITLE_STRS:
            if re.search(fr"(?:^|\s){bad}(?:\s|$)", self.title):
                return False
        if self.language_confidence < 0.95:
            return False
        if len(strip_cantillation(self.get_text(), strip_vowels=True)) < 200:
            return False

        return True

    def redetect_stupid_language(self, nlp):
        doc = nlp(self.get_text())
        self.language = doc._.language['language']
        self.language_confidence = doc._.language['score']

    def serialize(self):
        return f"{self.url}\n{self.title}\n{self.language} {self.language_confidence:{1}.{2}}\n{self.get_text()}"

    def save(self) -> None:
        with open(self.filename, 'w') as fout:
            fout.write(self.serialize())

    def delete(self) -> None:
        os.remove(self.filename)


def get_webpage(filename) -> Optional[ScrapedWebPage]:
    with open(filename, 'r') as fin:
        try:
            lines = [line.strip() for line in fin if len(line.strip()) > 0]
        except UnicodeDecodeError:
            print(filename, "isn't in UTF-8")
            return
        if len(lines) < 4:
            return  # no actual text
        try:
            lang, lang_confidence = lines[2].split()
        except ValueError:
            return  # title seems to be missing
        lang_confidence = float(lang_confidence)
        return ScrapedWebPage(
            url=lines[0],
            title=lines[1],
            language=lang,
            language_confidence=lang_confidence,
            text_lines=lines[3:],
            filename=filename
        )


def extract_webpages_output_dir(tar_name, output_dir):
    # try deleting output_dir if it exists
    shutil.rmtree(output_dir, ignore_errors=True)

    with tarfile.open(tar_name, 'r') as tin:
        tin.extractall(output_dir)


def compress_webpages_output_dir(input_dir, tar_name):
    with tarfile.open(tar_name, "w") as tout:
        for (dirpath, dirnames, filenames) in os.walk(input_dir):
            for filename in tqdm(filenames, desc='walk all webpages'):
                full_path = Path(dirpath).joinpath(filename)
                tout.add(full_path, arcname=filename)


def walk_all_webpages(dir, lang=None):
    for (dirpath, dirnames, filenames) in os.walk(dir):
        for filename in tqdm(filenames, desc='walk all webpages'):
            full_path = Path(dirpath).joinpath(filename)
            webpage = get_webpage(full_path)
            if lang is None or (webpage is not None and webpage.language == lang):
                yield webpage


def delete_bad_pages():
    count = 0
    for webpage in walk_all_webpages(DIR):
        if webpage is None:
            continue
        if not webpage.has_real_data():
            count += 1
            webpage.delete()
    print("num deleted", count)


def get_webpage_stats():
    hist_bucket_size = 0.05
    lang_counts = defaultdict(int)
    domain_counts = defaultdict(int)
    total_word_count = 0
    word_counts_by_lang = defaultdict(int)
    num_none = 0
    num_bad = 0
    num_deleted = 0
    conf_hist = defaultdict(int)
    for webpage in walk_all_webpages(DIR):
        if webpage is None:
            num_none += 1
            continue
        if not webpage.has_real_data():
            num_bad += 1
            continue

        from urllib.parse import urlparse
        domain = re.sub(r"^www\.", "", urlparse(webpage.url).netloc)
        domain_counts[domain] += 1
        lang_counts[webpage.language] += 1
        page_word_count = len(webpage.get_text().split())
        total_word_count += page_word_count
        word_counts_by_lang[webpage.language] += page_word_count
        conf_hist[math.floor(webpage.language_confidence/hist_bucket_size)] += 1

    for lang, count in sorted(lang_counts.items(), key=lambda x: x[1]):
        try:
            print(languages.get(alpha2=lang).name, f'({lang})', count)
            print("\t- word count", word_counts_by_lang[lang])
        except KeyError:
            print(lang, count)
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1]):
        print(domain, count)

    for conf_key, count in sorted(conf_hist.items(), key=lambda x: x[1]):
        print(f"{hist_bucket_size*conf_key}-{hist_bucket_size*(conf_key+1)}", count)
    print("num none", num_none)
    print("num bad", num_bad)
    print("num deleted", num_deleted)
    print("total word count", total_word_count)


if __name__ == '__main__':
    get_webpage_stats()
    # delete_bad_pages()
    # nlp = get_lang_detect_nlp()
    # for webpage in walk_all_webpages(DIR, lang='tl'):
    #     webpage.redetect_stupid_language(nlp)
    #     print(webpage.url)
    #     print(webpage.title)
    #     print(webpage.language)
    #     print(webpage.language_confidence)
    #     print(webpage.filename)