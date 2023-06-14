from util.helper import load_mongo_docs_or_json
import os
import argparse
from sefaria.utils.util import wrap_chars_with_overlaps
import srsly

GPT_PROMPT_END_INDICATOR = "\n\n###\n\n"


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output_filename')
    parser.add_argument('-i', '--input-type', dest='input_type')
    parser.add_argument('-m', '--db-host', dest='db_host')
    parser.add_argument('-p', '--db-port', dest='db_port', type=int)
    parser.add_argument("-u", "--user", dest="user", default="", nargs="?")
    parser.add_argument("-r", "--replicaset", dest="replicaset", default="", nargs="?")
    return parser


def create_gpt_training_prompts(citation_docs):
    return [
        {"prompt": create_get_prompt_input(doc), "completion": create_gpt_prompt_output(doc)}
        for doc in citation_docs
    ]


def get_wrapped_citation(citation, metadata):
    return f"[[{citation}]]", 2, 2


def create_get_prompt_input(citation_doc):
    return f"{citation_doc['text']} {GPT_PROMPT_END_INDICATOR}"


def create_gpt_prompt_output(citation_doc):
    chars_to_wrap = [(span['start'], span['end'], None) for span in citation_doc['spans']]
    return wrap_chars_with_overlaps(citation_doc['text'], chars_to_wrap, get_wrapped_citation)


if __name__ == '__main__':
    parser = init_argparse()
    args = parser.parse_args()
    password = os.getenv('MONGO_PASSWORD')
    citation_docs = load_mongo_docs_or_json(args.input, args.input_type, 0, True, args.db_host, args.db_port,
                                            args.user, password, args.replicaset)
    citation_docs = [doc for doc in citation_docs if doc['answer'] == 'accept']
    gpt_training = create_gpt_training_prompts(citation_docs)
    srsly.write_jsonl(args.output_filename, gpt_training)
