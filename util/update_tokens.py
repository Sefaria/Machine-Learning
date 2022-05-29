"""
Script to update tokens based on a new tokenizer
Assumes tokenizer name
"""
import argparse
from pymongo import InsertOne
from functools import reduce
from collections import defaultdict
import spacy_registry
from spacy import registry
from spacy.lang.en import English
from spacy.lang.he import Hebrew
from db_manager import MongoProdigyDBManager

def update_tokens_in_doc(doc: dict, tokenizer):
    updated_doc = doc.copy()
    updated_tokens = list(tokenizer(doc['text']))
    old_new_map = defaultdict(list)
    curr_old = 0
    for new_token in updated_tokens:
        old_token_dict = doc['tokens'][curr_old]
        if new_token.text == old_token_dict['text']:
            old_new_map[curr_old] += [new_token]
            assert new_token.idx == old_token_dict['start']
            assert new_token.idx + len(new_token) == old_token_dict['end']
            curr_old += 1
        else:
            matched_len = reduce(lambda a, b: a + len(b), old_new_map[curr_old], 0)
            old_text_to_match = old_token_dict['text'][matched_len:]
            if old_text_to_match.startswith(new_token.text):
                old_new_map[curr_old] += [new_token]
                if matched_len + len(new_token) == len(old_token_dict['text']):
                    assert old_new_map[curr_old][0].idx == old_token_dict['start']
                    assert new_token.idx + len(new_token) == old_token_dict['end']
                    curr_old += 1
            elif new_token.text.startswith(old_text_to_match):
                # flip matching direction. new_token is bigger than old token
                new_text_to_match = new_token.text
                while new_text_to_match.startswith(old_text_to_match):
                    old_new_map[curr_old] += [new_token]
                    curr_old += 1
                    new_text_to_match = new_text_to_match[len(old_text_to_match):]
                    old_text_to_match = doc['tokens'][curr_old]['text']
            else:
                raise Exception("something weird", old_text_to_match, new_token.text)
    updated_doc['tokens'] = [{
        "text": t.text,
        "start": t.idx,
        "end": t.idx + len(t),
        "id": t.i,
        "ws": len(t.whitespace_) > 0
    } for t in updated_tokens]
    updated_doc['spans'] = [update_span(old_span, old_new_map) for old_span in doc['spans']]
    return updated_doc

def update_span(old_span, old_new_map):
    new_start = old_new_map[old_span['token_start']][0]
    new_end = old_new_map[old_span['token_end']][-1]
    new_span = {
        "start": new_start.idx,
        "end": new_end.idx + len(new_end),
        "token_start": new_start.i,
        "token_end": new_end.i,
        "label": old_span['label']
    }
    # 'start' and 'end' should be the same. validate
    assert new_span['start'] == old_span['start']
    assert new_span['end'] == old_span['end']
    return new_span

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--tokenizer', dest='tokenizer_name', help='name of tokenizer in spacy_registry file')
    parser.add_argument('-i', '--input-collection', help='<Required> collection to convert', required=True, dest='input')
    parser.add_argument('-o', '--output-collection', help='<Required> output collection', required=True, dest='output')
    parser.add_argument('-l', '--lang', dest='lang')
    return parser

if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()
    nlp = Hebrew() if args.lang == 'he' else English()
    tokenizer = registry.tokenizers.get(args.tokenizer_name)()(nlp)
    input_db = MongoProdigyDBManager(args.input)
    output_db = MongoProdigyDBManager(args.output)
    output_db.output_collection.delete_many({})
    updated_docs = []
    for doc in input_db.output_collection.find({}):
        updated_docs += [update_tokens_in_doc(doc, tokenizer)]
    output_db.output_collection.bulk_write([InsertOne(doc) for doc in updated_docs])
