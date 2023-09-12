import django, json, argparse, os
django.setup()
from tqdm import tqdm
from collections import defaultdict
from helper import create_nlp, create_normalizer
from util.spacy_registry import get_lang_detect_nlp
from sefaria.model import *
from sefaria.system.exceptions import InputError


class TextWalker:

    def __init__(self, output_text, output_jsonl, lang, max_line_len=None, format='both', overlap=0, webpages_dir=None, with_metadata=False):
        self.output_text = output_text
        self.output_jsonl = output_jsonl
        self.lang = lang
        self.max_line_len = max_line_len
        self.format = format
        self.overlap = overlap
        self.webpages_dir = webpages_dir
        self.normalizer = create_normalizer()
        self.nlp = create_nlp(self.lang)
        self.with_metadata = with_metadata

    def write_lines(self, text, metadata=None):
        text = self.normalizer.normalize(text, lang=self.lang)
        if self.max_line_len is None:
            self.write_text(text, metadata)
        else:
            tokens = [token.text for token in self.nlp.tokenizer(text)]
            for i in range(0, len(tokens), self.max_line_len - self.overlap):
                line = " ".join(tokens[i:i + self.max_line_len])
                self.write_text(line, metadata)

    def write_text(self, text, metadata=None):
        if self.format in {'both', 'jsonl'}:
            data = {"text": text}
            if self.with_metadata:
                data['metadata'] = metadata
            self.output_jsonl.write(json.dumps(data) + '\n')
        if self.format in {'both', 'txt'}:
            self.output_text.write(text + '\n')

    def action(self, text, en_tref, he_tref, version):
        metadata = {
            "ref": en_tref, "versionTitle": version.versionTitle, "lang": version.actualLanguage,
            "docCategory": version.get_index().get_primary_category(),
            'dataQuality': 'user' if version.versionTitle == "Sefaria Community Translation" else 'professional'
        }
        self.write_lines(text, metadata=metadata)

    def walk_all_versions(self):
        query = {} if self.lang is None else {"language": self.lang}
        vs = VersionSet(query, limit=1)
        count = vs.count()
        for v in tqdm(vs, total=count):
            try:
                v.walk_thru_contents(self.action)
            except InputError:
                continue

    def walk_all_webpages(self):
        from util.webpages_util import walk_all_webpages, ScrapingError

        for webpage in walk_all_webpages(self.webpages_dir, self.lang):
            if webpage is ScrapingError: continue
            if webpage is None: continue
            if not webpage.has_real_data(): continue
            self.write_lines(webpage.get_text(), metadata={'dataQuality': "professional", "url": webpage.url, "lang": webpage.language})

    def walk_all_sheets(self):
        """
        outsideText, outsideBiText, comment
        :return:
        """
        from sefaria.system.database import db
        lang_counts = defaultdict(int)
        nlp = get_lang_detect_nlp()
        sheet_query = {"viaOwner": {"$exists": 0}, "assignment_id": {"$exists": 0}}
        num_public = db.sheets.count_documents(sheet_query)
        for sheet in tqdm(db.sheets.find(sheet_query), total=num_public):
            try:
                text = self.get_sheet_text(sheet)
            except:
                continue
            # TODO not clear we want to tag sheets by lang
            doc = nlp(text)
            lang = doc._.language['language']
            # lang_counts[lang] += 1
            # if lang != self.lang: continue
            self.write_lines(text, metadata={"lang": lang, "id": sheet['id'], "dataQuality": "user"})
        for lang, count in sorted(lang_counts.items(), key=lambda x: x[1]):
            print(lang, count)

    def get_sheet_text(self, sheet):
        text = [sheet.get('title', '')]
        for source in sheet['sources']:
            if "outsideBiText" in source:
                text.append(source['outsideBiText'].get('he', ''))
                text.append(source['outsideBiText'].get('en', ''))
            elif "text" in source:
                text.append(source['text'].get('he', ''))
                text.append(source['text'].get('en', ''))
            elif "outsideText" in source:
                text.append(source['outsideText'])
            elif "comment" in source:
                text.append(source['comment'])
        text = '\n'.join(text)
        text = self.normalizer.normalize(text, lang=self.lang)
        return text


def export_library_as_file(lang, output_stem, max_line_len=None, format='both', overlap=0, webpages_dir=None, with_source_sheets=False, with_metadata=False):
    output_text = open(f"{output_stem}.txt", "w")
    output_jsonl = open(f"{output_stem}.jsonl", "w")

    walker = TextWalker(output_text, output_jsonl, lang, max_line_len=max_line_len, format=format, overlap=overlap, webpages_dir=webpages_dir, with_metadata=with_metadata)
    walker.walk_all_versions()
    if webpages_dir is not None:
        walker.walk_all_webpages()
    # if with_source_sheets:
    #     walker.walk_all_sheets()

    output_text.close()
    output_jsonl.close()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('lang', help='either a lang code or "all"')
    parser.add_argument('-f', '--format', dest='format', help='"both", "jsonl" or "txt"')
    parser.add_argument('-w', '--webpages-dir', dest='webpages_dir')
    parser.add_argument('-s', '--with-sheets', dest='with_sheets', action='store_true')
    parser.add_argument('-o', '--output', dest='output')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    lang = None if args.lang == 'all' else args.lang
    export_library_as_file(lang, args.output, max_line_len=None, overlap=0, webpages_dir=args.webpages_dir, format=args.format, with_source_sheets=args.with_sheets, with_metadata=True)

