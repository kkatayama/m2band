# from rich import inspect
import hashlib
import codecs
import json
import os


###############################################################################
#                              CREATE OPERATIONS                              #
###############################################################################
def insertRow(db, query="", **kwargs):
    """
    query = "INSERT INTO users (username,password,create_time) VALUES (?, ?, ?) RETURNING user_id;"
    cur   = db.execute(query, [username, hash_pass, create_time])
    """
    table     = kwargs["table"]
    columns   = ",".join(kwargs["columns"])
    values    = kwargs["values"]
    if not query:
        query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['?']*len(columns))});"
    cur = db.execute(query, values)
    if cur:
        return cur.lastrowid
    return False

###############################################################################
#                               READ OPERATIONS                               #
###############################################################################
def fetchRow(db, query="", **kwargs):
    table     = kwargs.get("table")
    columns   = "*" if not kwargs.get("columns") else ",".join(kwargs["columns"])
    condition = "TRUE" if not kwargs.get("where") else f'({kwargs["where"]})'
    values    = kwargs.get("values")
    if not query:
        query = f"SELECT {columns} FROM {table} WHERE {condition};"
    row = db.execute(query, values).fetchone() if values else db.execute(query).fetchone()
    if row:
        return dict(row)
    return False

def fetchRows(db, query="", **kwargs):
    table     = kwargs.get("table")
    columns   = "*" if not kwargs.get("columns") else ",".join(kwargs["columns"])
    condition = "TRUE" if not kwargs.get("where") else f'({kwargs["where"]})'
    values    = kwargs.get("values")
    if not query:
        query = f"SELECT {columns} FROM {table} WHERE {condition};"
    rows = db.execute(query, values).fetchall() if values else db.execute(query).fetchall()
    if rows:
        return [dict(row) for row in rows]
    return False

###############################################################################
#                              UPDATE OPERATIONS                              #
###############################################################################


###############################################################################
#                              DELETE OPERATIONS                              #
###############################################################################


# Helper Functions ############################################################

def securePassword(plaintext):
    salt = os.urandom(32)
    digest = hashlib.pbkdf2_hmac("sha256", plaintext.encode(), salt, 1000)
    hex_salt = codecs.encode(salt, "hex").decode()
    hex_digest = digest.hex()
    hex_pass = hex_salt + hex_digest
    return hex_pass

def checkPassword(plaintext, hex_pass):
    hex_salt = hex_pass[:64]
    hex_digest = hex_pass[64:]
    salt = codecs.decode(hex_salt, "hex")
    digest = codecs.decode(hex_digest, "hex")
    test_digest = hashlib.pbkdf2_hmac("sha256", plaintext.encode(), salt, 1000)
    if test_digest == digest:
        return True
    return False

def clean(data):
    return json.loads(json.dumps(data, default=str))
