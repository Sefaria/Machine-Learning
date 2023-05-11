from typing import List
from helper import get_mongo_docs
from sklearn.model_selection import train_test_split

def get_train_test_data(random_state: int, mongo_docs: List[dict], training_percentage: float):
    train_data, test_data = train_test_split(mongo_docs, random_state=random_state, train_size=training_percentage)
    return train_data, test_data


def get_corpus_data(db_host: str, db_port: int, input_collection: str, random_state: int, train_perc: float, corpus_type: str, min_len: int, unique_by_metadata=True):
    data = get_mongo_docs(min_len, unique_by_metadata, input_collection, db_host, db_port)
    print("Num examples", len(data))
    if random_state == -1:
        train_data, test_data = (data, []) if corpus_type == "train" else ([], data)
    else:
        train_data, test_data = get_train_test_data(random_state, data, train_perc)
    corpus_data = train_data if corpus_type == "train" else test_data
    return corpus_data
