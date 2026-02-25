import shelve

from config import DB_PATH

class PersistentDict:
    def __init__(self, name):
        self.filename = name

    def __getitem__(self, key):
        with shelve.open(self.filename, writeback=True) as db:
            return db[key]

    def __setitem__(self, key, value):
        with shelve.open(self.filename, writeback=True) as db:
            db[key] = value
            db.sync()

    def __delitem__(self, key):
        with shelve.open(self.filename, writeback=True) as db:
            del db[key]
            db.sync()

    def get(self, key, default=None):
        with shelve.open(self.filename, writeback=True) as db:
            return db.get(key, default)

    def keys(self):
        with shelve.open(self.filename, writeback=True) as db:
            return list(db.keys())

    def values(self):
        with shelve.open(self.filename, writeback=True) as db:
            return list(db.values())

    def items(self):
        with shelve.open(self.filename, writeback=True) as db:
            return list(db.items())

    def __contains__(self, key):
        with shelve.open(self.filename, writeback=True) as db:
            return key in db

    def clear(self):
        with shelve.open(self.filename, writeback=True) as db:
            db.clear()
            db.sync()
