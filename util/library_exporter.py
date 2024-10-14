import django, json, argparse, os
import srsly

django.setup()
from tqdm import tqdm
from collections import defaultdict
from helper import create_nlp, create_normalizer
from util.spacy_registry import get_lang_detect_nlp
from sefaria.model import *
from sefaria.system.exceptions import InputError
import pandas as pd
from pathlib import Path


class TextWalker:

    def __init__(self, output_text, output_jsonl, lang, max_line_len=None, format='both', overlap=0, webpages_dir=None,
                 with_metadata=False, responsa_dir=None):
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
        self.responsa_dir = responsa_dir
        self._word_count = 0
        self._ref_pr_map = {ref_data.ref: ref_data.pagesheetrank for ref_data in RefDataSet()}

    def write_lines(self, text, metadata=None):
        text = self.normalizer.normalize(text, lang=self.lang)
        self._word_count += len(text.split())
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
            self.output_text.write(text + '\n----\n')

    def get_word_count(self):
        return self._word_count

    def action(self, text, en_tref, he_tref, version):
        oref = Ref(en_tref)
        metadata = {
            "url": f"https://www.sefaria.org/{oref.url()}",
            "ref": en_tref, "versionTitle": version.versionTitle, "lang": version.actualLanguage,
            "docCategory": version.get_index().get_primary_category(),
            'dataQuality': 'user' if version.versionTitle == "Sefaria Community Translation" else 'professional',
            'pagerank': self._ref_pr_map.get(en_tref, RefData.DEFAULT_PAGESHEETRANK),
        }
        self.write_lines(text, metadata=metadata)

    def walk_all_versions(self):
        query = {} if self.lang is None else {"actualLanguage": self.lang}
        vs = VersionSet(query)
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
                sheet['id']
            except:
                continue
            # TODO not clear we want to tag sheets by lang
            try:
                doc = nlp(text[:2000])
                lang = doc._.language['language']
            except ValueError:
                continue
            # lang_counts[lang] += 1
            # if lang != self.lang: continue
            self.write_lines(text, metadata={"lang": lang, "id": sheet['id'], "url": f"https://www.sefaria.org/sheets/{sheet['id']}", "dataQuality": "user"})
        for lang, count in sorted(lang_counts.items(), key=lambda x: x[1]):
            print(lang, count)

    def walk_all_responsa(self):
        self._walk_all_moreshet()
        self._walk_all_aviner()
        self._walk_all_kipa()
        self._walk_all_yeshiva_co_il()

    def _walk_all_moreshet(self):
        df = pd.read_excel(f"{self.responsa_dir}/moreshet responsa.xlsx")
        for row in df.itertuples():
            line = f"{row.Title}.\n{row.Cateory}.\n{row.Question}\n{row.Answer}"
            self.write_lines(line, metadata={'dataQuality': "professional", "url": row.Link, "lang": "he"})

    def _walk_all_aviner(self):
        df = pd.read_excel(f"{self.responsa_dir}/Rav Aviner Responsa.xlsx", sheet_name="Data")
        for row in df.itertuples():
            self.write_lines(row.Text, metadata={'dataQuality': "professional", "lang": "he", "source": "Rav Aviner Responsa"})

    def _walk_all_kipa(self):
        for (dirpath, dirnames, filenames) in os.walk(f"{self.responsa_dir}/index-kipa"):
            for filename in tqdm(filenames, desc='walk all kipa'):
                full_path = Path(dirpath).joinpath(filename)
                try:
                    df = pd.read_excel(full_path)
                except ValueError:
                    print(filename)
                    continue
                for irow, row in enumerate(df.itertuples()):
                    line = f"{row[3]}.\n{row[4]}\n{row[5]}"
                    self.write_lines(line, metadata={'dataQuality': "professional", "lang": "he", "source": "kipa.co.il responsa"})

    def _walk_all_yeshiva_co_il(self):
        import mysql.connector
        cnx = mysql.connector.connect(user='root', password=os.getenv("MYSQL_PASSWORD"), host='localhost',
                                      database='yeshiva')
        query = "SELECT QuestionText, Answer, Title FROM combined_csv"
        df = pd.read_sql(query, cnx)
        line = f"{df.Title}.\n{df.QuestionText}\n{df.Answer}"
        self.write_lines(line, metadata={'dataQuality': "professional", "lang": "he", "source": "yeshiva.co.il responsa"})

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


def export_library_as_file(lang, output_stem, max_line_len=None, format='both', overlap=0, webpages_dir=None, with_source_sheets=False, with_metadata=False, responsa_dir=None):
    output_text = open(f"{output_stem}.txt", "w")
    output_jsonl = open(f"{output_stem}.jsonl", "w")

    walker = TextWalker(output_text, output_jsonl, lang, max_line_len=max_line_len, format=format, overlap=overlap, webpages_dir=webpages_dir, with_metadata=with_metadata, responsa_dir=responsa_dir)
    walker.walk_all_versions()
    if webpages_dir is not None:
        walker.walk_all_webpages()
    if with_source_sheets:
        walker.walk_all_sheets()
    if responsa_dir is not None:
        walker.walk_all_responsa()

    output_text.close()
    output_jsonl.close()
    print('Word count: {:,}'.format(walker.get_word_count()))


def export_all_links():
    from sefaria.pagesheetrank import init_pagerank_graph

    graph, _ = init_pagerank_graph()
    out = []
    filtered_out = []
    for tref1, linked_tref_dict in tqdm(graph.items(), desc="all links"):
        for tref2 in linked_tref_dict.keys():
            out += [{"to": tref1, "from": tref2}]
            if tref1.startswith("Mishneh Torah, ") or tref2.startswith("Mishneh Torah, "):
                filtered_out += [out[-1]]
    srsly.write_jsonl("/Users/nss/Downloads/all_links.jsonl", out)
    srsly.write_jsonl("/Users/nss/Downloads/mishneh_torah_links.jsonl", filtered_out)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('lang', help='either a lang code or "all"')
    parser.add_argument('-f', '--format', dest='format', help='"both", "jsonl" or "txt"')
    parser.add_argument('-w', '--webpages-dir', dest='webpages_dir')
    parser.add_argument('-r', '--responsa-dir', dest='responsa_dir')
    parser.add_argument('-s', '--with-sheets', dest='with_sheets', action='store_true')
    parser.add_argument('-o', '--output', dest='output')
    return parser.parse_args()


if __name__ == '__main__':
    args = get_args()
    lang = None if args.lang == 'all' else args.lang
    export_library_as_file(lang, args.output, max_line_len=None, overlap=0, webpages_dir=args.webpages_dir,
                           format=args.format, with_source_sheets=args.with_sheets, with_metadata=True,
                           responsa_dir=args.responsa_dir)
    export_all_links()

