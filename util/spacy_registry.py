import spacy
import re
from spacy.tokenizer import Tokenizer
from spacy.language import Language
from spacy_langdetect import LanguageDetector


@spacy.registry.tokenizers("inner_punct_tokenizer")
def inner_punct_tokenizer_factory():
    def inner_punct_tokenizer(nlp):
        # infix_re = spacy.util.compile_infix_regex(nlp.Defaults.infixes)
        infix_re = re.compile(r'''[\.\,\?\:\;…\‘\’\`\“\”\"\'~\–\-/\(\)]''')
        prefix_re = spacy.util.compile_prefix_regex(nlp.Defaults.prefixes)
        suffix_re = spacy.util.compile_suffix_regex(nlp.Defaults.suffixes)

        return Tokenizer(nlp.vocab, prefix_search=prefix_re.search,
                         suffix_search=suffix_re.search,
                         infix_finditer=infix_re.finditer,
                         token_match=None)
    return inner_punct_tokenizer


@Language.factory("language_detector")
def create_language_detector(nlp, name):
    return LanguageDetector(language_detection_function=None)


def get_lang_detect_nlp():
    spacy.prefer_gpu()
    nlp = spacy.load('en_core_web_sm')
    nlp.add_pipe('language_detector', last=True)
    return nlp
