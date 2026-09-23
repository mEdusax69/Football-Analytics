"""
MongoDB NoSQL Storage Module
------------------------------
Provides full CRUD (Create, Read, Update, Delete) over the player
dataset as JSON-style documents.

If a real MongoDB server is reachable (via `pymongo`), this connects
to it directly. Otherwise it falls back to `LocalDocumentStore`, a
drop-in, file-backed document store with the same
insert/find/update/delete interface, a JSON collection file, and
Mongo-style query filters (dict matching, $gt/$lt/$in operators) --
so the rest of the project (dashboard, reports) works unmodified
whether or not a real Mongo instance is present.
"""

import json
import os
from copy import deepcopy


# ----------------------------------------------------------------------
# Fallback: local JSON-backed document store with a Mongo-like API
# ----------------------------------------------------------------------
class LocalDocumentStore:
    """A minimal Mongo-collection-compatible store, persisted as JSON."""

    def __init__(self, path: str):
        self.path = path
        if os.path.exists(path):
            with open(path) as f:
                self.docs = json.load(f)
        else:
            self.docs = []

    def _save(self):
        with open(self.path, "w") as f:
            json.dump(self.docs, f, indent=2)

    @staticmethod
    def _matches(doc, query):
        for key, cond in query.items():
            val = doc.get(key)
            if isinstance(cond, dict):
                for op, target in cond.items():
                    if op == "$gt" and not (val is not None and val > target):
                        return False
                    if op == "$gte" and not (val is not None and val >= target):
                        return False
                    if op == "$lt" and not (val is not None and val < target):
                        return False
                    if op == "$lte" and not (val is not None and val <= target):
                        return False
                    if op == "$in" and val not in target:
                        return False
                    if op == "$ne" and val == target:
                        return False
            else:
                if val != cond:
                    return False
        return True

    # ---- CREATE --------------------------------------------------------
    def insert_one(self, doc: dict):
        doc = deepcopy(doc)
        self.docs.append(doc)
        self._save()
        return doc

    def insert_many(self, docs):
        docs = [deepcopy(d) for d in docs]
        self.docs.extend(docs)
        self._save()
        return docs

    # ---- READ ------------------------------------------------------------
    def find(self, query: dict = None, limit: int = None):
        query = query or {}
        results = [d for d in self.docs if self._matches(d, query)]
        if limit:
            results = results[:limit]
        return results

    def find_one(self, query: dict = None):
        results = self.find(query, limit=1)
        return results[0] if results else None

    def count_documents(self, query: dict = None):
        return len(self.find(query))

    # ---- UPDATE ------------------------------------------------------------
    def update_one(self, query: dict, update: dict):
        for doc in self.docs:
            if self._matches(doc, query):
                doc.update(update.get("$set", update))
                self._save()
                return True
        return False

    def update_many(self, query: dict, update: dict):
        count = 0
        for doc in self.docs:
            if self._matches(doc, query):
                doc.update(update.get("$set", update))
                count += 1
        if count:
            self._save()
        return count

    # ---- DELETE --------------------------------------------------------
    def delete_one(self, query: dict):
        for i, doc in enumerate(self.docs):
            if self._matches(doc, query):
                del self.docs[i]
                self._save()
                return True
        return False

    def delete_many(self, query: dict):
        before = len(self.docs)
        self.docs = [d for d in self.docs if not self._matches(d, query)]
        self._save()
        return before - len(self.docs)


# ----------------------------------------------------------------------
# Unified wrapper: tries real MongoDB, falls back to LocalDocumentStore
# ----------------------------------------------------------------------
class PlayerNoSQLStore:
    def __init__(self, json_fallback_path=None,
                 mongo_uri="mongodb://localhost:27017/",
                 db_name="football_analytics", collection_name="players"):
        if json_fallback_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            json_fallback_path = os.path.join(base_dir, "..", "data", "mongo_players.json")
        self.backend = "mongodb"
        try:
            import pymongo
            client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
            client.server_info()  # forces connection check
            self.collection = client[db_name][collection_name]
            print("[MongoDB] Connected to a real MongoDB instance.")
        except Exception:
            self.backend = "local_simulation"
            self.collection = LocalDocumentStore(json_fallback_path)
            print("[MongoDB] No live MongoDB server found -- using "
                  "LocalDocumentStore simulation (same CRUD API, "
                  f"JSON-backed at {json_fallback_path}).")

    def load_from_dataframe(self, df, reset=True):
        if reset:
            if self.backend == "mongodb":
                self.collection.delete_many({})
            else:
                self.collection.docs = []
                self.collection._save()
        records = df.to_dict(orient="records")
        self.collection.insert_many(records)
        print(f"[MongoDB:{self.backend}] Inserted {len(records)} player documents")

    # Convenience CRUD passthroughs
    def create(self, doc):
        return self.collection.insert_one(doc)

    def read(self, query=None, limit=None):
        return list(self.collection.find(query or {}, limit) if limit
                    else self.collection.find(query or {}))

    def update(self, query, changes):
        return self.collection.update_one(query, {"$set": changes})

    def delete(self, query):
        return self.collection.delete_one(query)

    def count(self, query=None):
        return self.collection.count_documents(query or {})


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("../data/football_players_cleaned.csv")
    store = PlayerNoSQLStore()
    store.load_from_dataframe(df)

    print("\nTotal documents:", store.count())

    # CREATE
    store.create({
        "player_id": 9999, "player_name": "Test Player", "team": "Test FC",
        "position": "Forward", "goals": 10, "rating": 7.9,
    })
    print("After insert:", store.count())

    # READ
    forwards = store.read({"position": "Forward"}, limit=3)
    print("Sample forwards:", [p["player_name"] for p in forwards])

    # UPDATE
    store.update({"player_id": 9999}, {"goals": 15})
    print("After update:", store.read({"player_id": 9999}))

    # DELETE
    store.delete({"player_id": 9999})
    print("After delete:", store.count())
