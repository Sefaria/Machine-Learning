"""
Functions for analyzing models
"""

import spacy, srsly, json, csv, django, typer
django.setup()
from sefaria.model import *
from functools import reduce
from tqdm import tqdm
from util.training_utils import get_corpus_data, get_train_test_data
from spacy.lang.en import English
from spacy.lang.he import Hebrew
from util.spacy_registry import inner_punct_tokenizer_factory
from sefaria.utils.util import wrap_chars_with_overlaps
from util.helper import get_window_around_match, generate_example_stream, load_mongo_docs


def id_to_gen(_id):
    if _id is None:
        return 'N/A'
    if _id.startswith('http'):
        return 'web'
    else:
        try:
            oref = Ref(_id)
        except:
            return 'N/A'
        # return "|".join(oref.index.authors)
        try:
            tp = oref.index.best_time_period()
        except:
            tp = None
        if tp is not None and isinstance(tp.start, int) and tp.start < 1500:
            return 'rishonim'
        else:
            return 'achronim'


def make_evaluation_files(evaluation_data, ner_model, output_folder, start=0, lang='he', only_errors=False):
    from collections import defaultdict
    tp, fp, fn, tn = 0, 0, 0, 0
    eval_by_gen = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
    eval_by_label = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0, "tn": 0})

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
            eval_by_gen[id_to_gen(example.predicted.user_data.get('Ref', None))][metric] += len(temp)
            for _, _, predicted_label in temp:
                eval_by_label[predicted_label][metric] += 1
        if only_errors and (len(temp_fn) + len(temp_fp)) == 0:
            continue
        output_json += [{
            "text": doc.text,
            "tp": [list(ent) for ent in temp_tp],
            "fp": [list(ent) for ent in temp_fp],
            "fn": [list(ent) for ent in temp_fn],
            "meta": example.predicted.user_data,
        }]

    srsly.write_jsonl(f"{output_folder}/doc_evaluation.jsonl", output_json)
    make_evaluation_html(output_json, output_folder, 'doc_evaluation.html', lang)
    print('PRECISION', 100 * round(tp / (tp + fp), 4))
    print('RECALL   ', 100 * round(tp / (tp + fn), 4))
    print('F1       ', 100 * round(tp / (tp + 0.5 * (fp + fn)), 4))

    for gen, metrics in eval_by_gen.items():
        output_accuracy_metrics(gen, metrics)
    for label, metrics in eval_by_label.items():
        output_accuracy_metrics(label, metrics)
    return tp, fp, tn, fn


def output_accuracy_metrics(title, metrics):
    total = reduce(lambda a, b: a + b, metrics.values(), 0)
    if total == 0: return
    print('-----', title, '-----')
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
            "answer": example.predicted.user_data.get('answer', "accept"),
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
    make_evaluation_csv(output_json, output_folder, 'doc_export.csv')


def make_evaluation_csv(data, output_folder, output_filename):
    rows = []
    for i, d in enumerate(data):
        named_entities = reduce(lambda a, b: a + [(ne + [b]) for ne in d[b]], ('tp', 'fp', 'fn'), [])
        named_entities.sort(key=lambda x: x[0])
        for j, (start, end, label, truthiness) in enumerate(named_entities):
            prev_end = 0 if j == 0 else named_entities[j-1][1]
            next_start = None if (j == len(named_entities) - 1) else named_entities[j+1][0]
            rows += [{
                "Ref": d['meta'].get('ref', '') if 'meta' in d else d.get('ref', ''),
                'Named Entity': d['text'][start:end],
                'Label': label,
                'Status': truthiness,
                'Text Before': d['text'][prev_end:start],
                'Text After': d['text'][end:next_start],
            }]
    with open(f"{output_folder}/{output_filename}", "w") as fout:
        cout = csv.DictWriter(fout, ['Ref', 'Text Before', 'Named Entity', 'Text After', 'Label', 'Status'])
        cout.writeheader()
        cout.writerows(rows)


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
        .answer-reject { background-color: pink; }
        .answer-accept { background-color: greenyellow; }
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
        <p class="ref answer-{d.get('answer', 'accept')}">{i}) {d.get('ref', '')} - ID: {d.get('_id', '')}</p>
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


def main(task: str, lang: str, collection_name: str, model_dir: str = None, db_host: str = "localhost", db_port: int = 27017,
         random_state: int = 61, train_perc: float = 0.8, min_len: int = 20):
    if task == "evaluate model":
        nlp = spacy.load(model_dir)
        docs = get_corpus_data(db_host, db_port, collection_name, random_state, train_perc, "test", min_len, include_reject=True)
        evaluated_docs = generate_example_stream(nlp, docs)
        print(make_evaluation_files(evaluated_docs, nlp, './output/evaluation_results', lang=lang, only_errors=False))
    elif task == "export tagged data":
        nlp = English() if lang == "en" else Hebrew()
        nlp.tokenizer = inner_punct_tokenizer_factory()(nlp)
        docs = get_corpus_data(db_host, db_port, collection_name, -1, 0, "test", min_len, include_reject=False)
        exported_docs = generate_example_stream(nlp, docs)
        export_tagged_data_as_html(exported_docs, './output/evaluation_results', is_binary=False, start=0, lang=lang)
    elif task == "output data to refine":
        pass
        ## Output test data to collection to refine in prodigy
        ## This code hasn't been run in a while and doesn't work. Keeping hear for legacy.
        # data = get_corpus_data('localhost', 27017, 'merged_output', 'gilyon_input', 61, 0.5, 'test', 20)
        # dbm = MongoProdigyDBManager("test_data_to_refine")
        # dbm.output_collection.delete_many({})
        # dbm.output_collection.bulk_write([InsertOne(x) for x in data])
    else:
        print("No task matched")


if __name__ == "__main__":
    typer.run(main)

"""
prodigy ner-recipe ref_tagging ner_en_gpt_output_copper ner_en_gpt_silver Citation,Person,Group -lang en -dir ltr --view-id ner_manual
"""