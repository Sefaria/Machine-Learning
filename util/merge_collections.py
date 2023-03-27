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
    parser.add_argument('-m', '--mongohost', dest='mongo_host')
    parser.add_argument('-p', '--mongoport', dest='mongo_port', type=int)
    parser.add_argument("-u", "--user", dest="user", const="", nargs="?")
    parser.add_argument("-pw", "--password", dest="password", const="", nargs="?")
    parser.add_argument("-r", "--replicaset", dest="replicaset", const="", nargs="?")
    parser.add_argument('-c', '--input-collections', nargs='+', help='<Required> List of collections to combine', required=True, dest='input')
    return parser

if __name__ == "__main__":
    parser = init_argparse()
    args = parser.parse_args()
    print("Input Collections:", ", ".join(args.input))
    print("Output Collection:", args.output)
    print(args)
    output_db = MongoProdigyDBManager(args.output, host=args.mongo_host, port=args.mongo_port, user=args.user, password=args.password, replicaset_name=args.replicaset)
    output_db.output_collection.delete_many({})
    all_docs = []
    unique_keys = set()
    for in_collection in args.input:
        in_collection, limit = in_collection.split(':') if ':' in in_collection else (in_collection, None)
        limit = limit if limit is None else int(limit)
        input_db = MongoProdigyDBManager(in_collection, host=args.mongo_host, port=args.mongo_port, user=args.user, password=args.password, replicaset_name=args.replicaset)
        temp_docs = list(input_db.output_collection.find({}))[:limit]
        for doc in temp_docs:
            key = (tuple(sorted(doc['meta'].items(), key=lambda x: x[0])), doc['text'])
            if key in unique_keys: continue
            unique_keys.add(key)
            all_docs += [doc]
    output_db.output_collection.bulk_write([InsertOne(doc) for doc in all_docs])
