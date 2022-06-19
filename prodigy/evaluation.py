"""
Functions for analyzing models
"""

from typing import Callable, Iterator, List
import spacy, re, srsly, json, csv, django
django.setup()
from sefaria.model import *
from functools import reduce
from tqdm import tqdm
from prodigy.functions import stream_data
from util.spacy_registry import inner_punct_tokenizer_factory

def id_to_gen(_id):
    if _id.startswith('http'):
        return 'web'
    else:
        oref = Ref(_id)
        # return "|".join(oref.index.authors)
        tp = oref.index.best_time_period()
        if tp.start < 1500:
            return 'rishonim'
        else:
            return 'achronim'


def make_evaluation_files(evaluation_data, ner_model, output_folder, start=0, lang='he', only_errors=False):
    from collections import defaultdict
    tp, fp, fn, tn = 0, 0, 0, 0
    eval_by_gen = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    data_tuples = [(eg.text, eg) for eg in evaluation_data]
    output_json = []
    # see https://spacy.io/api/language#pipe
    for iexample, (doc, example) in enumerate(tqdm(ner_model.pipe(data_tuples, as_tuples=True))):
        if iexample < start: continue
        # correct_ents
        ents_x2y = example.get_aligned_spans_x2y(example.reference.ents)
        correct_ents = {(e.start_char, e.end_char, e.label_) for e in ents_x2y}
        # predicted_ents
        ents_x2y = example.get_aligned_spans_x2y(doc.ents)
        predicted_ents = {(e.start_char, e.end_char, e.label_) for e in ents_x2y}
        # false positives
        temp_fp = [ent for ent in predicted_ents if ent not in correct_ents]
        fp += len(temp_fp)
        # true positives
        temp_tp = [ent for ent in predicted_ents if ent in correct_ents]
        tp += len(temp_tp)
        # false negatives
        temp_fn = [ent for ent in correct_ents if ent not in predicted_ents]
        fn += len(temp_fn)
        # true negatives
        temp_tn = [ent for ent in correct_ents if ent in predicted_ents]
        tn += len(temp_tn)

        # breakdown by gen
        for metric, temp in zip(('tp', 'fp', 'fn', 'tn'), (temp_tp, temp_fp, temp_fn, temp_tn)):
            # TODO relies on Sefaria-Project but prodigy server doesn't have access to that code
            # TODO consider moving evaluation code to another file
            eval_by_gen[id_to_gen(example.predicted.user_data['Ref'])][metric] += len(temp)
        if only_errors and (len(temp_fn) + len(temp_fp)) == 0:
            continue
        output_json += [{
            "text": doc.text,
            "tp": [list(ent) for ent in temp_tp],
            "fp": [list(ent) for ent in temp_fp],
            "fn": [list(ent) for ent in temp_fn],
            "ref": example.predicted.user_data['Ref'],
            "_id": example.predicted.user_data['_id'],
        }]

    srsly.write_jsonl(f"{output_folder}/doc_evaluation.jsonl", output_json)
    make_evaluation_html(output_json, output_folder, 'doc_evaluation.html', lang)
    print('PRECISION', 100 * round(tp / (tp + fp), 4))
    print('RECALL   ', 100 * round(tp / (tp + fn), 4))
    print('F1       ', 100 * round(tp / (tp + 0.5 * (fp + fn)), 4))

    for gen, metrics in eval_by_gen.items():
        total = reduce(lambda a, b: a + b, metrics.values(), 0)
        if total == 0: continue
        print('-----', gen, '-----')
        print('Total    ', total)
        try:
            print('PRECISION', 100 * round(metrics['tp'] / (metrics['tp'] + metrics['fp']), 4))
        except ZeroDivisionError:
            print('PRECISION N/A')
        try:
            print('RECALL   ', 100 * round(metrics['tp'] / (metrics['tp'] + metrics['fn']), 4))
        except ZeroDivisionError:
            print('RECALL    N/A')
        try:
            print('F1       ', 100 * round(metrics['tp'] / (metrics['tp'] + 0.5 * (metrics['fp'] + metrics['fn'])), 4))
        except ZeroDivisionError:
            print('F1        N/A')
    return tp, fp, tn, fn


def export_tagged_data_as_html(tagged_data, output_folder, is_binary=True, start=0, lang='he'):
    output_json = []
    for iexample, example in enumerate(tagged_data):
        if iexample < start: continue
        ents_x2y = example.get_aligned_spans_x2y(example.reference.ents)
        out_item = {
            "text": "",
            "tp": [],
            "fp": [],
            "fn": [],
            "ref": example.predicted.user_data['Ref'],
            "_id": example.predicted.user_data['_id'],
        }
        if is_binary:
            assert len(ents_x2y) == 1
            span = ents_x2y[0]
            before, after = get_window_around_match(span.start_char, span.end_char, example.text)
            span_text = example.text[span.start_char:span.end_char]
            trimmed_text = f"{before} {span_text} {after}"
            new_start = len(before) + 1
            new_end = new_start + len(span_text)
            tp, fp = ([[new_start, new_end, span.label_]], []) if example.predicted.user_data[
                                                                      'answer'] == "accept" else (
            [], [[new_start, new_end, span.label_]])
            out_item.update(dict(text=trimmed_text, tp=tp, fp=fp))
        else:
            out_item['text'] = example.text
            out_item['tp'] = [[span.start_char, span.end_char, span.label_] for span in ents_x2y]
        output_json += [out_item]
    make_evaluation_html(output_json, output_folder, 'doc_export.html', lang)


def wrap_chars_with_overlaps(s, chars_to_wrap, get_wrapped_text, return_chars_to_wrap=False):
    chars_to_wrap.sort(key=lambda x: (x[0], x[0] - x[1]))
    for i, (start, end, metadata) in enumerate(chars_to_wrap):
        wrapped_text, start_added, end_added = get_wrapped_text(s[start:end], metadata)
        s = s[:start] + wrapped_text + s[end:]
        chars_to_wrap[i] = (start, end + start_added + end_added, metadata)
        for j, (start2, end2, metadata2) in enumerate(chars_to_wrap[i + 1:]):
            if start2 >= end:
                start2 += end_added
            start2 += start_added
            if end2 > end:
                end2 += end_added
            end2 += start_added
            chars_to_wrap[i + j + 1] = (start2, end2, metadata2)
    if return_chars_to_wrap:
        return s, chars_to_wrap
    return s


def make_evaluation_html(data, output_folder, output_filename, lang='he'):
    html = """
    <html>
      <head>
        <style>
        body { max-width: 800px; margin-right: auto; margin-left: auto; }
        .doc { line-height: 200%; border-bottom: 2px black solid; padding-bottom: 20px; }
        .tag { padding: 5px; }
        .tp { background-color: greenyellow; border: 5px lightgreen solid; }
        .fp { background-color: pink; border: 5px lightgreen solid; }
        .fn { background-color: greenyellow; border: 5px pink solid; }
        .label { font-weight: bold; font-size: 75%; color: #666; padding-right: 5px; }
        </style>
      </head>
      <body>
    """

    def get_wrapped_text(mention, metadata):
        start = f'<span class="{metadata["true condition"]} tag">'
        end = f'<span class="label">{metadata["label"]}</span></span>'
        return f'{start}{mention}{end}', len(start), len(end)

    for i, d in enumerate(data):
        chars_to_wrap = [(s, e, {"label": l, "true condition": 'tp'}) for (s, e, l) in d['tp']]
        chars_to_wrap += [(s, e, {"label": l, "true condition": 'fp'}) for (s, e, l) in d['fp']]
        chars_to_wrap += [(s, e, {"label": l, "true condition": 'fn'}) for (s, e, l) in d['fn']]
        wrapped_text = wrap_chars_with_overlaps(d['text'], chars_to_wrap, get_wrapped_text)
        html += f"""
        <p class="ref">{i}) {d['ref']} - ID: {d['_id']}</p>
        <p dir="{'rtl' if lang == 'he' else 'ltr'}" class="doc">{wrapped_text}</p>
        """
    html += """
      </body>
    </html>
    """
    with open(f"{output_folder}/{output_filename}", "w") as fout:
        fout.write(html)


def convert_jsonl_to_json(filename):
    j = list(srsly.read_jsonl(filename))
    with open(filename[:-1], 'w') as fout:
        json.dump(j, fout, ensure_ascii=False, indent=2)


def get_window_around_match(start, end, text, window=10):
    before_window, after_window = '', ''

    before_text = text[:start]
    before_window_words = list(filter(lambda x: len(x) > 0, before_text.split()))[-window:]
    before_window = " ".join(before_window_words)

    after_text = text[end:]
    after_window_words = list(filter(lambda x: len(x) > 0, after_text.split()))[:window]
    after_window = " ".join(after_window_words)

    return before_window, after_window


def convert_jsonl_to_csv(filename):
    j = srsly.read_jsonl(filename)
    rows = []
    for d in j:
        algo_guesses = {(s, e) for s, e, _ in (d['fp'] + d['tp'])}
        false_negs = {(s, e) for s, e, _ in d['fn']}
        all_algo_inds = set()
        for start, end in algo_guesses:
            all_algo_inds |= set(range(start, end))
        missed_tags = set()
        for start, end in false_negs:
            temp_inds = set(range(start, end))
            if len(temp_inds & all_algo_inds) == 0:
                missed_tags.add((start, end))
        for algo_missed, temp_data in zip(['n', 'y'], [algo_guesses, missed_tags]):
            for start, end in temp_data:
                before, after = get_window_around_match(start, end, d['text'])
                match = d['text'][start:end]
                rows += [{
                    "Before": before,
                    "After": after,
                    "Citation": match,
                    "Algorithm Missed": algo_missed
                }]

    with open(filename[:-5] + '.csv', 'w') as fout:
        c = csv.DictWriter(fout, ['Type', 'Correct?', 'Algorithm Missed', 'After', 'Citation', 'Before'])
        c.writeheader()
        c.writerows(rows)


if __name__ == "__main__":
    # nlp = spacy.load('./output/yerushalmi_refs/model-last')
    # nlp = spacy.load('./output/webpages/model-last')
    # nlp = spacy.load('/home/nss/sefaria/ML/linker/models/webpages_he_achronim/model-last')
    nlp = spacy.load('/home/nss/sefaria/ML/linker/models/ner_en/model-last')
    data = stream_data('localhost', 27017, 'merged_output', 'gilyon_input', 61, 0.8, 'test', 20)(nlp)
    print(make_evaluation_files(data, nlp, './temp', lang='en', only_errors=True))

    # data = stream_data('localhost', 27017, 'yerushalmi_output', 'gilyon_input', -1, 1.0, 'train', 0, unique_by_metadata=True)(nlp)
    # export_tagged_data_as_html(data, './output/evaluation_results', is_binary=False, start=0, lang='en')  # 897
    # convert_jsonl_to_json('./output/evaluation_results/doc_evaluation.jsonl')
    # convert_jsonl_to_csv('./output/evaluation_results/doc_evaluation.jsonl')
    # spacy.training.offsets_to_biluo_tags(doc, entities)
