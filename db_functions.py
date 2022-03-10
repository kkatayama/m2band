# from rich import inspect
import hashlib
import codecs
import os


###############################################################################
#                              CREATE OPERATIONS                              #
###############################################################################
def insertRow(db, table="", columns=[], query="", query_params=[]):
    """
    Insert data into the database

    Args:
        Required - db (object)          - the database connection object
        Required - table (str)          - the table to fetch data from          - (ex: "users")
        Optional - columns (list)       - filter each row to these columns      - (ex: ["user_id", "username"])
        Optional - query (str)          - SQL query, "table" not required
        Required - query_params (list)  - variables to be used with "query" or "columns"
    Returns:
        id (int) or False - the ID for the transaction (for "users" table, this is the "user_id")
    """
    if not query:
        query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['?']*len(columns))});"
    cur = db.execute(query, query_params)
    if cur:
        return cur.lastrowid
    return False

###############################################################################
#                               READ OPERATIONS                               #
###############################################################################
def fetchRows(db, table="", columns=[], query="", condition="", query_params=[]):
    """
    Fetch multiple rows from a table in the database.

    Args:
        Required - db (object)          - the database connection object
        Required - table (str)          - the table to fetch data from          - (ex: "users")
        Optional - columns (list)       - filter each row to these columns      - (ex: ["user_id", "username"])
        Optional - query (str)          - SQL query, "table" not required
        Optional - condition (str)      - adds a "WHERE" clause (query_params)  - (ex: "username=?")
        Optional - query_params (list)  - variables to be used with "query" or "condition"
    Returns:
        rows (list of dict objects) or False
    """
    if query:
        if query_params:
            rows = db.execute(query, query_params).fetchall()
        else:
            rows = db.execute(query).fetchall()
    else:
        query = f"SELECT * FROM {table};"
        if columns:
            query = query.replace("*", ",".join(columns), 1)
        if condition:
            query = query.replace(";", f" WHERE {condition};", 1)
        if query_params:
            rows = db.execute(query, query_params).fetchall()
        else:
            rows = db.execute(query).fetchall()

    print(query)
    if rows:
        return [dict(row) for row in rows]
    return False


def fetchRow(db, table="", columns=[], query="", condition="", query_params=[]):
    """
    Fetch a single row from a table in the database.

    Args:
        Required - db (object)          - the database connection object
        Required - table (str)          - the table to fetch data from          - (ex: "users")
        Optional - columns (list)       - filter each row to these columns      - (ex: ["user_id", "username"])
        Optional - query (str)          - SQL query, "table" not required
        Optional - condition (str)      - adds a "WHERE" clause (query_params)  - (ex: "username=?")
        Optional - query_params (list)  - variables to be used with "query" or "condition"
    Returns:
        row (dict object) or False
    """
    if query:
        if query_params:
            row = db.execute(query, query_params).fetchone()
        else:
            row = db.execute(query).fetchone()
    else:
        query = f"SELECT * FROM {table};"
        if columns:
            query = query.replace('*', ','.join(columns))
        if condition:
            query = query.replace(";", f" WHERE {condition};", 1)
        if query_params:
            row = db.execute(query, query_params).fetchone()
        else:
            row = db.execute(query).fetchone()

    print(query)
    if row:
        return dict(row)
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
