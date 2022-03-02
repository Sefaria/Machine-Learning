import django, json, argparse
django.setup()
from tqdm import tqdm

from util.spacy_registry import inner_punct_tokenizer_factory
from spacy.lang.en import English
from spacy.lang.he import Hebrew
from sefaria.model import *
from sefaria.system.exceptions import InputError
from sefaria.helper.normalization import NormalizerByLang, NormalizerComposer

class TextWalker:

    def __init__(self, output, lang, max_line_len=None, format='txt', overlap=0):
        self.output = output
        self.lang = lang
        self.max_line_len = max_line_len
        self.format = format
        self.overlap = overlap
        base_normalizer_steps = ['unidecode', 'html', 'double-space']
        self.normalizer = NormalizerByLang({
            'en': NormalizerComposer(base_normalizer_steps),
            'he': NormalizerComposer(base_normalizer_steps + ['maqaf', 'cantillation']),
        })
        self.nlp = self.create_nlp()

    def create_nlp(self):
        """
        Create nlp object for tokenization
        :return:
        """
        nlp = Hebrew() if self.lang == 'he' else English()
        nlp.tokenizer = inner_punct_tokenizer_factory()(nlp)
        return nlp

    def write_lines(self, text):
        text = self.normalizer.normalize(text, lang=self.lang)
        if self.max_line_len is None:
            self.write_text(text)
        else:
            tokens = [token.text for token in self.nlp.tokenizer(text)]
            for i in range(0, len(tokens), self.max_line_len - self.overlap):
                line = " ".join(tokens[i:i + self.max_line_len])
                self.write_text(line)

    def write_text(self, text):
        if self.format == 'jsonl':
            text = json.dumps({"text": text})
        self.output.write(text + '\n')

    def action(self, text, en_tref, he_tref, version):
        self.write_lines(text)

def export_library_as_file(lang, output_stem, max_line_len=None, format='txt', overlap=0, webpages_text=None):
    vs = VersionSet({"language": lang})
    count = vs.count()
    output_fname = f"{output_stem}.{format}"
    output = open(output_fname, "w")
    walker = TextWalker(output, lang, max_line_len=max_line_len, format=format, overlap=overlap)
    for v in tqdm(vs, total=count):
        if v.versionTitle[-5:-3] == ' [':
            continue
        try:
            v.walk_thru_contents(walker.action)
        except InputError:
            continue
    if webpages_text is not None:
        with open(webpages_text, 'r') as fin:
            for line in fin:
                walker.write_lines(line)

    output.close()

"""
# Currently unused

def export_library_without_prefixes_as_file():
    output = open("all_text_he_no_prefixes_old.txt", "w")
    walker = TextWalker(output, 'he')
    with open(f"{DATA_LOC}/prefix_with_refs.json", "r") as fin:
        j = json.load(fin)
    word_count = 0
    unique_words = set()
    for ref, text in tqdm(j.items(), total=len(j)):
        text = normalize(remove_prefixes(text), 'he')
        if len(text) == 0:
            continue
        word_count += len(text.split())
        for word in text.split():
            unique_words.add(word)
        walker.write_text(text)
    output.close()
    print("Unique words:", len(unique_words))
    print("Total words:", word_count)

def remove_prefixes(s):
    normalized = ""
    for word in s.split():
        word = re.sub(r"^[^|]+\|", "", word)
        normalized += ' ' + word
    return normalized

class BiWalker:
    def __init__(self, bi_data):
        self.bi_data = bi_data
    def action(self, text, en_tref, he_tref, version):
        if 'en' not in self.bi_data[en_tref]:
            self.bi_data[en_tref]['en'] = ''
        self.bi_data[en_tref]['en'] += normalize(text, 'en') + " "

def export_library_as_csv():
    with open(f"{DATA_LOC}/prefix_with_refs.json", "r") as fin:
        j = json.load(fin)
    from collections import defaultdict
    bi_data = defaultdict(dict)
    for ref, text in tqdm(j.items(), total=len(j)):
        text = normalize(remove_prefixes(text), 'he')
        try:
            oref = Ref(ref)
        except InputError:
            continue
        bi_data[ref]['book'] = oref.index.title
        if len(text) == 0:
            continue
        bi_data[ref]['he'] = text
    vs = VersionSet({"language": 'en'})
    count = vs.count()
    walker = BiWalker(bi_data)
    for v in tqdm(vs, total=count):
        if v.versionTitle[-5:-3] == ' [':
            continue 
        try:
            v.walk_thru_contents(walker.action)
        except InputError:
            continue
    rows = [{"Ref": ref, "He": s.get('he', ''), "En": s.get('en', ''), "Book": s.get('book', '')} for ref, s in bi_data.items() if (len(s.get('en', '')) > 0 or len(s.get('he', '')) > 0)]
    with open(f"{DATA_LOC}/en_and_he_without_prefixes.csv", "w") as fout:
        c = csv.DictWriter(fout, ["Ref", "He", "En", "Book"])
        c.writeheader()
        c.writerows(rows)
        
def export_links_as_file():
    ls = LinkSet().array()
    output = open("all_links.txt", "w")
    for l in tqdm(ls):
        try:
            Ref(l.refs[0])
        except InputError:
            continue
        try:
            Ref(l.refs[1])
        except InputError:
            continue
        if len(l.expandedRefs0) * len(l.expandedRefs1) > 300:
            print("SKIPPING", l.refs[0], l.refs[1])
            continue
        for ll in l.expandedRefs0:
            for mm in l.expandedRefs1:
                output.write(f"{ll}|||{mm}\n")
    # ls = None
    # for i in tqdm(library.all_index_records()):
    #     refs = i.all_segment_refs()
    #     for i in range(len(refs)-1):
    #         ref1, ref2 = refs[i:i+2]
    #         output.write(f"{ref1.normal()}|||{ref2.normal()}\n")

    output.close()

def export_responsa_as_file():
    import os
    with open('/home/nss/sefaria/datasets/general/responsa-all.txt', 'w') as fout:
        for root, dirs, files in os.walk("/home/nss/sefaria/datasets/general/responsa"):
            for name in files:
                fin = open(os.path.join(root, name), 'r')
                for line in fin:
                    if len(line.strip()) == 0 or line.startswith('### '):
                        continue
                    fout.write(line)
                fin.close()
"""

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('lang')
    parser.add_argument('-f', '--format', dest='format', help='"both", "jsonl" or "txt"')
    parser.add_argument('-w', '--webpages-data', dest='webpages_data')
    parser.add_argument('-o', '--output', dest='output')
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    formats = [args.format] if args.format != 'both' else ['txt', 'jsonl']
    for f in formats:
        export_library_as_file(args.lang, args.output, max_line_len=512, overlap=50, webpages_text=args.webpages_data, format=f)

