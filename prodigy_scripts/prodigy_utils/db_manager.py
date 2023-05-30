from pymongo import MongoClient
import urllib.parse

class MongoProdigyDBManager:

    def __init__(self, output_collection, host='localhost', port=27017, user="", password="", replicaset_name=""):
        self.client = MongoProdigyDBManager.init_client(host, port, user, password, replicaset_name)
        self.db_name = "prodigy"
        self.db = getattr(self.client, self.db_name)
        self.output_collection = getattr(self.db, output_collection)

    @classmethod
    def init_client(cls, host, port, user, password, replicaset_name):
        # If we have jsut a single instance mongo (such as for development) the host param should contain jsut the host string e.g "localhost")
        if replicaset_name == "":
            if user and password:
                return MongoClient(host, port, username=user, password=password)
            else:
                return MongoClient(host, port)
        # Else if we are using a replica set mongo, we need to connect with a URI that containts a comma separated list of 'host:port' strings
        else:
            if user and password:
                # and also escape user/pass
                username = urllib.parse.quote_plus(user)
                password = urllib.parse.quote_plus(password)
                connection_uri = 'mongodb://{}:{}@{}/?ssl=false&readPreference="secondaryPreferred"&replicaSet={}'.format(
                    username, password, host, replicaset_name)
            else:
                connection_uri = 'mongodb://{}/?ssl=false&readPreference="secondaryPreferred"&replicaSet={}'.format(
                    host, replicaset_name)
            # Now connect to the mongo server
            print(f"URI: {connection_uri}")
            return MongoClient(connection_uri)

    def get_dataset(self, name):
        return list(self.output_collection.find({"datasets": name}))
    
    def __len__(self):
        return len(self.datasets)

    def __contains__(self, name):
        return self.db.datasets.find_one({"name": name}) is not None

    def get_meta(self, name):
        pass

    def get_examples(self, ids, by="_task_hash"):
        return list(self.output_collection.find({by: {"$in": ids}}))

    def get_input_hashes(self, *names):
        examples = self.output_collection.find({"datasets": {"$in": names}})
        return {ex['_input_hash'] for ex in examples}

    def get_task_hashes(self, *names):
        examples = self.output_collection.find({"datasets": {"$in": names}})
        return {ex['_task_hash'] for ex in examples}

    def count_dataset(self, name, session=False):
        return self.output_collection.count_documents({"datasets": name})

    def add_dataset(self, name, meta=None, session=False):
        if self.db.datasets.find_one({"name": name}) is not None:
            # already exists
            return self.get_dataset(name)
        meta = meta or {}
        dataset = {
            "name": name,
            "meta": meta,
            "session": session
        }
        self.db.datasets.insert_one(dataset)
        return []

    def add_examples(self, examples, datasets):
        if len(examples) == 0:
            return
        for example in examples:
            example['datasets'] = datasets
        self.output_collection.insert_many(examples)

    def link(self, name, example_ids):
        for _id in example_ids:
            example = self.output_collection.find_one({"_id": _id})
            example['datasets'] = example.get('datasets', [])
            example['datasets'] += [name]
            self.output_collection.update_one({"_id": _id}, example)

    def unlink(self, example_ids):
        for _id in example_ids:
            example = self.output_collection.find_one({"_id": _id})
            example['datasets'] = []
            self.output_collection.update_one({"_id": _id}, example)

    def drop_dataset(self, name, batch_size):
        self.db.datasets.delete_one({"name": name})
        for example in self.output_collection.find({"datasets": name}):
            example['datasets'] = list(filter(lambda x: x != name, example['datasets']))
            self.output_collection.update_one({"_id": example['_id']}, example)
        return True

    def get_datasets(self):
        return [dataset['name'] for dataset in self.db.datasets.find({"session": False})]

    def get_sessions(self):
        return [dataset['name'] for dataset in self.db.datasets.find({"session": True})]

    datasets = property(get_datasets)
    sessions = property(get_sessions)

db_manager = MongoProdigyDBManager('silver_output_binary')