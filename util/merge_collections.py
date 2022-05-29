"""
Utility for merging multiple collections into one
Currently limited to collections in 'prodigy' db (for no particular reason except that's the only use-case right now)
"""

from db_manager import MongoProdigyDBManager
from pymongo import InsertOne
import argparse

def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--output-collection', dest='output', help='name of output collection')
    parser.add_argument('-c', '--input-collections', nargs='+', help='<Required> List of collections to combine', required=True, dest='input')
    return parser

if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    print("Input Collections:", ", ".join(args.input))
    print("Output Collection:", args.output)
    output_db = MongoProdigyDBManager(args.output)
    output_db.output_collection.delete_many({})
    all_docs = []
    unique_keys = set()
    for in_collection in args.input:
        in_collection, limit = in_collection.split(':') if ':' in in_collection else (in_collection, None)
        limit = limit if limit is None else int(limit)
        input_db = MongoProdigyDBManager(in_collection)
        temp_docs = list(input_db.output_collection.find({}))[:limit]
        for doc in temp_docs:
            key = (tuple(sorted(doc['meta'].items(), key=lambda x: x[0])), doc['text'])
            if key in unique_keys: continue
            unique_keys.add(key)
            all_docs += [doc]
    output_db.output_collection.bulk_write([InsertOne(doc) for doc in all_docs])
