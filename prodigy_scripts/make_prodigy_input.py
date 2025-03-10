import django, regex, srsly, random, re
from os import walk, path
from collections import defaultdict
from tqdm import tqdm
import argparse
django.setup()
from sefaria.model import *
from sefaria.system.exceptions import InputError
from db_manager import MongoProdigyDBManager
from sefaria.helper.normalization import NormalizerComposer


class ProdigyInputWalker:
    def __init__(self, prev_tagged_refs=None, with_links=False, preprocess_input=None, min_links=None):
        self.prodigyInput = []
        self.prodigyInputByVersion = defaultdict(list)
        self.with_links = with_links
        self.min_links = min_links
        self.prev_tagged_refs = prev_tagged_refs or []
        self.normalizer = NormalizerComposer(['unidecode', 'br-tag', 'itag' ,'html', 'maqaf', 'cantillation', 'double-space'])
        if preprocess_input:
            self.preprocess_input = preprocess_input
        else:
            self.preprocess_input = self.default_preprocesser


    @staticmethod
    def get_refs_with_location(text, lang, citing_only=True):
        unique_titles = set(library.get_titles_in_string(text, lang, citing_only))
        title_node_dict = {title: library.get_schema_node(title,lang) for title in unique_titles}
        titles_regex_str = library.get_multi_title_regex_string(unique_titles, lang)
        titles_regex = regex.compile(titles_regex_str, regex.VERBOSE)
        
        def get_ref_from_match(match, outer_start=0):
            try:
                gs = match.groupdict()
                assert gs.get("title") is not None
                node = title_node_dict[gs.get("title")]
                ref = library._get_ref_from_match(match, node, lang)
                return ref.normal(), match.group(0), match.start(0)+outer_start, match.end(0)+outer_start
            except InputError:
                return None
            except AssertionError:
                return None
            except ValueError:
                return None
            except KeyError:
                return None

        refs_with_loc = []
        if lang == "en":
            refs_with_loc = [get_ref_from_match(m) for m in titles_regex.finditer(text)]
        else:
            outer_regex_str = r"[({\[].+?[)}\]]"
            outer_regex = regex.compile(outer_regex_str, regex.VERBOSE)
            for outer_match in outer_regex.finditer(text):
                refs_with_loc += [get_ref_from_match(m, outer_match.start(0)) for m in titles_regex.finditer(outer_match.group(0))]
        refs_with_loc = list(filter(None, refs_with_loc))
        return refs_with_loc

    def split_text(self, text):
        return text.split('. ')

    def get_itag_texts(self, text):
        from sefaria.helper.normalization import ITagNormalizer

        itags, _ = ITagNormalizer._get_all_itags(text)
        itag_texts = [itag.decode() for itag in itags]
        return [itag_text for itag_text in itag_texts if len(itag_text) > 20]

    def default_preprocesser(self, text):
        itag_texts = self.get_itag_texts(text)
        try:
            text = self.normalizer.normalize(text)
            text_list = text.split('\n')
        except Exception as e:
            print(e)
            text_list = []
        text_list += [self.normalizer.normalize(itag_text).strip() for itag_text in itag_texts]
        return text_list

    def get_input(self, text, en_tref, language):
        text_list = self.preprocess_input(text)
        temp_input_list = []
        for t in text_list:
            if len(t) <= 20: continue
            refs_with_loc = ProdigyInputWalker.get_refs_with_location(t, language) if (self.with_links or self.min_links) else []
            if self.min_links is not None and len(refs_with_loc) < self.min_links:
                continue
            temp_input = {
                "text": t,
                "spans": [
                    {"start": s, "end": e, "label": "Citation"} for _, _, s, e in (refs_with_loc if self.with_links else [])
                ],
                "meta": {
                    "Ref": en_tref
                }
            }
            temp_input_list += [temp_input]
        return temp_input_list

    def action(self, text, en_tref, he_tref, version):
        if en_tref in self.prev_tagged_refs:
            print("ignoring", en_tref)
            return
        # text = TextChunk._strip_itags(text)
        temp_input_list = self.get_input(text, en_tref, version.language)
        self.prodigyInputByVersion[(version.versionTitle, version.title, version.language)] += temp_input_list
        
    def make_final_input(self, sample_size, max_length=None):
        import statistics
        lens = []
        for temp_input_list in self.prodigyInputByVersion.values():
            lens += [len(t['text']) for t in temp_input_list]
            if max_length is not None:
                temp_input_list = [t for t in temp_input_list if len(t['text']) < max_length]
            self.prodigyInput += random.sample(temp_input_list, min(len(temp_input_list), sample_size))
        print(statistics.mean(lens))
        print(statistics.stdev(lens))
        random.shuffle(self.prodigyInput)


def make_random_prodigy_input(lang, prev_tagged_refs, collection, with_links=False, sample_size=100, max_length=None):
    walker = ProdigyInputWalker(prev_tagged_refs, with_links)
    versions = VersionSet({"language": lang}).array()
    for version in tqdm(versions):
        if re.search(r'\[[a-zA-Z]+]$', version.versionTitle): continue
        try:
            version.walk_thru_contents(walker.action)
        except InputError:
            continue
    walker.make_final_input(sample_size, max_length=max_length)
    import_data_to_collection(walker.prodigyInput, collection)


def make_prodigy_input_index(title_list, vtitle_list, lang_list, prev_tagged_refs, collection, with_links=False,
                       preprocess=None, max_prodigy_input=None, min_links=None):
    walker = ProdigyInputWalker(prev_tagged_refs, with_links, preprocess_input=preprocess, min_links=min_links)
    for title, vtitle, lang in tqdm(zip(title_list, vtitle_list, lang_list), total=len(title_list)):
        if vtitle is None:
            versions = VersionSet({"title": title, "language": lang}, sort=[("priority", -1)], limit=1).array()
            if len(versions) == 0:
                continue
            version = versions[0]
        else:
            version = Version().load({"title": title, "versionTitle": vtitle, "language": lang})
        version.walk_thru_contents(walker.action)
    walker.make_final_input(400)
    if max_prodigy_input:
        walker.prodigyInput = walker.prodigyInput[:max_prodigy_input]
    import_data_to_collection(walker.prodigyInput, collection)


def import_data_to_collection(data, collection, db_host='localhost', db_port=27017):
    my_db = MongoProdigyDBManager('blah', db_host, db_port)
    getattr(my_db.db, collection).delete_many({})
    getattr(my_db.db, collection).insert_many(data)


def num_english_chars(s, perc=True):
    num = 0
    for match in re.finditer(r'[a-zA-Z]', s):
        num += (match.end() - match.start())
    if perc and len(s) > 0:
        return num / len(s)
    return num


def make_prodigy_input_webpages(n, lang, collection, prev_tagged_urls=None):
    from util.webpages_util import walk_all_webpages
    prev_tagged_urls = set(prev_tagged_urls) or set()
    walker = ProdigyInputWalker()
    nchosen = 0
    for webpage in walk_all_webpages("../web_scraper/output", lang):
        if not webpage.has_real_data() or webpage.url in prev_tagged_urls:
            continue
        # Seemingly we should continue if chosen is False. Not sure why that isn't happening.
        chosen = random.choice([True, False])
        if nchosen >= n: break
        nchosen += int(chosen)
        walker.prodigyInput += walker.get_input(webpage.get_text(), webpage.url, lang)
    random.shuffle(walker.prodigyInput)
    import_data_to_collection(walker.prodigyInput, collection)


def combine_sentences_to_paragraph(sentences):
    if len(sentences) == 0: return
    full_text = ""
    full_spans = []
    curr_tokens = 0
    already_seen_text = set()
    for s in sentences:
        if s['text'] in already_seen_text: continue
        already_seen_text.add(s['text'])
        if len(full_text) > 0: full_text += " "
        full_spans += [{
            "start": span['start'] + len(full_text),
            "end": span['end'] + len(full_text),
            "token_start": span['token_start'] + curr_tokens,
            "token_end": span['token_end'] + curr_tokens,
            "label": span['label']
        } for span in s['spans']]
        curr_tokens += len(s['tokens'])
        full_text += s['text']
    return {
        'text': full_text,
        'spans': full_spans,
        'meta': sentences[0]['meta']
    }


def combine_all_sentences_to_paragraphs():
    my_db = MongoProdigyDBManager('blah', 'localhost', 27017)
    examples = my_db.db.examples
    combined_examples = []
    examples_by_ref = defaultdict(list)
    for example in examples.find({}):
        examples_by_ref[example['meta']['Ref']] += [example]
    combined_examples = [combine_sentences_to_paragraph(sentences) for sentences in examples_by_ref.values()]
    my_db.db.examples1_input.delete_many({})
    my_db.db.examples1_input.insert_many(combined_examples)


def make_prodigy_input_by_refs(ref_list, lang, vtitle):
    walker = ProdigyInputWalker([])
    input_list = []
    for tref in ref_list:
        oref = Ref(tref)
        text = walker.normalizer.normalize(oref.text(lang, vtitle=vtitle).text)
        temp_input_list = walker.get_input(text, tref, lang)
        input_list += temp_input_list
    srsly.write_jsonl('data/test_input.jsonl', input_list)


def make_prodigy_input_sub_citation(citation_collection, output_collection, skip=0):
    my_db = MongoProdigyDBManager('blah', 'localhost', 27017)
    getattr(my_db.db, output_collection).delete_many({})
    for doc in getattr(my_db.db, citation_collection).find({}).skip(skip):
        for span in doc['spans']:
            if span['label'] != 'Citation': continue
            span_text = doc['text'][span['start']:span['end']]
            getattr(my_db.db, output_collection).insert_one({"text": span_text, "spans": [], "meta": {"Ref": doc['meta']['Ref'], "Start": span['start'], "End": span['end']}})


def get_prev_tagged_refs(collection_name):
    if collection_name is None:
        return set()
    my_db = MongoProdigyDBManager(collection_name, 'localhost', 27017)
    return set(my_db.output_collection.find({}).distinct('meta.Ref'))


if __name__ == "__main__":
    pass
    # TODO these commands may still be useful. If they are, pull out args for them.
    # make_random_prodigy_input('en', prev_tagged_refs, 'ner_en_input', max_length=1500)
    # combine_all_sentences_to_paragraphs()
    make_prodigy_input_sub_citation('ner_en_gpt_copper_combo', 'ner_en_gpt_copper_combo_sub_citation')
