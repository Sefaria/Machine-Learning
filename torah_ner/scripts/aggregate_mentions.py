import django, json, srsly, csv

django.setup()
from sefaria.model import *
from tqdm import tqdm
from spacy.lang.he import Hebrew
from sefaria.spacy_function_registry import inner_punct_tokenizer_factory
from sefaria.model.linker.ref_part import span_inds
from util.helper import create_normalizer

import typer
import subprocess
import yaml
# "
# {
#     "text": <text of segment>,
#     "spans": [<see definition of span below>],
#     "meta": {
#         "Ref": <ref>,
#         "Version Title": <version title>,
#         "Language": <language>
#     }
# }"
#
# "
# {
#     "start": <start character of mention>,
#     "end": <end character of mention>,
#     "token_start": <start token of mention>,
#     "token_end": <end token of mention>,
#     "label": "Person"
# }"


def get_token_start_and_end_for_char_start_and_end(segment_string, char_start, char_end):
    doc = nlp(segment_string)
    tokens = [token.text for token in doc]
    # print(tokens)

    span = doc.char_span(char_start, char_end)  # may raise error if char_start or char_end don't land on token boundary
    indices = ("failed", "failed")
    try:
        indices = span_inds(span)
        return indices
    except:
        dummy = 1


    # range_parameter = 3;
    # for i in range(char_start - range_parameter, char_end):
    #     for j in range(char_start, char_end + range_parameter):
    #         new_char_start = i
    #         new_char_end = j
    #
    #         try:
    #             span = doc.char_span(new_char_start, new_char_end)
    #             indices = span_inds(span)
    #             return indices
    #         except:
    #             dummy = 1

    return indices


def normalize_text(non_normal_char_start, non_normal_char_end, non_normal_text):

    # input
    language = "he"  # or "en"
    # non_normal_char_indices = [(start1, end1), (start2, end2)...]  # your char indices from mentions.json
    non_normal_char_indices = [(non_normal_char_start, non_normal_char_end)]

    normalizer = create_normalizer()
    normal_text = normalizer.normalize(non_normal_text, lang=language)  # language is either "he" or "en"
    mapping = normalizer.get_mapping_after_normalization(non_normal_text, reverse=True, lang=language)

    # output
    normal_char_indices = normalizer.convert_normalized_indices_to_unnormalized_indices(non_normal_char_indices, mapping,
                                                                                        reverse=True)
    return (normal_text, normal_char_indices[0][0], normal_char_indices[0][1])

def separate_aggregated_by_language(agg_list):
    agg_en = []
    agg_he = []

    for mention in tqdm(agg_list, desc="separating mentions"):

        if mention["meta"]["language"] == "en":
            agg_en.append(mention)
        elif mention["meta"]["language"] == "he":
            agg_he.append(mention)

    return agg_en, agg_he

def aggregate(raw_mentions_filename: str, output_file_title: str):
    # stats
    problematic_count = 0
    sane_count = 0
    all_count = 0


    with open(raw_mentions_filename) as f:
        mentions = json.load(f)

    aggregated_list = []
    aggregated_dict = {}

    problematic_mention = []

    for mention in tqdm(mentions, desc="aggregating mentions"):

        all_count += 1
        segment = Ref(mention["ref"]).text(vtitle=mention["versionTitle"], lang=mention["language"]).text
        start_char = mention["start"]
        end_char = mention["end"]
        normal_segment, normal_char_start, normal_char_end = normalize_text(start_char, end_char, segment)
        start_token, end_token = get_token_start_and_end_for_char_start_and_end(normal_segment, normal_char_start,
                                                                                normal_char_end)
        
        if start_token == "failed":
            problematic_mention.append(mention)
            problematic_count += 1
            continue
        end_token = end_token - 1  # for some reason, spacy expects end_token to be minus one
        sane_count += 1
        key = mention["ref"] + "$" + mention["versionTitle"]

        # index = next((i for i, item in enumerate(aggregated_list) if item["meta"]["ref"] == mention["ref"] and item["meta"]["version_title"] == mention["versionTitle"]), -1)

        # if index == -1:

        if key not in aggregated_dict:
            new_spans_array = [{
                "start": normal_char_start,
                "end": normal_char_end,
                "token_start": start_token,
                "token_end": end_token,
                "label": "Person"
            }]

            new_agg_item = {
                "text": normal_segment,
                "spans": new_spans_array,
                "meta": {
                    "ref": mention["ref"],
                    "version_title": mention["versionTitle"],
                    "language": mention["language"]
                }
            }
            # aggregated_list.append(new_agg_item)
            aggregated_dict[key] = new_agg_item

        else:
            new_spans_item = {
                "start": normal_char_start,
                "end": normal_char_end,
                "token_start": start_token,
                "token_end": end_token,
                "label": "Person"
            }
            # aggregated_list[index]["spans"].append(new_spans_item)
            aggregated_dict[key]["spans"].append(new_spans_item)

    aggregated_list = list(aggregated_dict.values())
    agg_en, agg_he = separate_aggregated_by_language(aggregated_list)
    with open(output_file_title + "_en.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(agg_en, f, ensure_ascii=False, indent=2)
    with open(output_file_title + "_he.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(agg_he, f, ensure_ascii=False, indent=2)

    with open("problematic.json", "w") as f:
        # Write the list of dictionaries to the file as JSON
        json.dump(problematic_mention, f, ensure_ascii=False, indent=2)
    print("sane mentions count = " + str(sane_count))
    print("problematic mentions count = " + str(problematic_count))
    print("all mentions count = " + str(all_count))
    print("percentage of sane: " + str((sane_count / all_count) * 100) + "%")
    print("finish")


if __name__ == "__main__":
    nlp = Hebrew()
    nlp.tokenizer = inner_punct_tokenizer_factory()(nlp)
    print("hello world")
    typer.run(aggregate)
