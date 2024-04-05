import sqlite3
import os
from config import DATABASE

def get_db():
    db = sqlite3.connect(os.path.join(os.getcwd(), "db", DATABASE), detect_types=sqlite3.PARSE_DECLTYPES)
    db.row_factory = sqlite3.Row
    return db

def close_db():
    # Suppression de l'attribut 'db' dans l'objet g
    db = g.pop('db', None)

    # Au cas où la suppression n'aurait pas fonctionné, on ferme la connexion.
    if db is not None:
        db.close()