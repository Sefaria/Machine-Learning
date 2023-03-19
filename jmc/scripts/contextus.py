import sys
from sefaria.helper.normalization import *
print(sys.path)
import bleach
from prodigy.make_prodigy_input import *
from evaluation import *
#
nlp = English()
nlp.tokenizer = inner_punct_tokenizer_factory()(nlp)
data = stream_data('localhost', 27017, 'contextus_output', -1, 1.0, 'train', 20, unique_by_metadata=True)(nlp)
export_tagged_data_as_html(data, './', is_binary=False, start=0, lang='en')

def likely_citations(x):
    if (re.search("\(.{8,}\)", x) or re.search("<i class", x)) or "clause" in x or "chapter" in x or "section" in x:
        x = x.replace("\n", " ")
        results = ITagNormalizer._get_all_itags(x)
        tags, soup = results
        for tag in tags[::-1]:
            if tag.name == "i":
                x = x.replace(str(tag), " "+tag.text+" ", 1)
            else:
                assert str(tag) in x
                x = x.replace(str(tag), "", 1)

        x = bleach.clean(x, tags=[], strip=True)
        while "  " in x:
            x = x.replace("  ", " ")
        return [x.strip()]
    else:
        return []

# #sys.path = ['/opt/homebrew/lib/python3.9/site-packages']+sys.path
# from make_prodigy_input import *
# # Federalist Papers, Madison's Notes
# # remove i tags
# title_list = []
# title_list += [i.title for i in IndexSet({"categories": "Commentaries on the US Constitutional Regime"})]
# title_list += [i.title for i in IndexSet({"categories": "The Federalist Papers"})]
# title_list += ["Madison's Notes on the Constitutional Convention"]
# # print(title_list)
# #make_random_prodigy_input('en', prev_tagged_refs, 'ner_en_input', max_length=1500)
# make_prodigy_input(title_list, [None]*len(title_list), ['en']*len(title_list), set(), 'contextus_input',
#                    preprocess=likely_citations, maxProdigyInput=300)
# # make_prodigy_input_webpages(3000, prev_tagged_refs)
#combine_all_sentences_to_paragraphs()
# make_prodigy_input_sub_citation('webpages_output', 'webpages_sub_citation_input2')
