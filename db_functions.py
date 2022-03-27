"""
# Overview of DB Functions #
These functions connect to the SQLite Database and execute transactions.
All functions use "parametrized queries" to prevent SQL injection attacks.
All functions support a full SQL [query] or a python [dict]

# -- insertRow()    - Insert data into the database
# -- fetchRow()     - Fetch a single row from a table in the database
# -- fetchRows()    - Fetch multiple rows from a table in the database
# -- updateRow()    - Update data in the database
# -- deleteRow()    - Delete row(s) from the database

# Overview of Helper Functions #
# -- securePassword()   - create a password (sha256 hash, salt, and iterate)
# -- checkPassword()    - check if password matches
# -- clean()            - sanitize data for json delivery
"""
from bottle import request, response
from datetime import datetime
from functools import wraps
import logging
import sqlite3
import hashlib
import codecs
import json
import os
import re

###############################################################################
#                              CREATE OPERATIONS                              #
###############################################################################
def insertRow(db, query="", **kwargs):
    """
    Insert data into the database

    ARGS:
        Required - db (object)          - the database connection object
        Optional - query (str)          - a complete SQL query

        Required - table (str)          - the table to insert data into
        Required - columns (list)       - the columns to edit
        Required - col_values (list)    - the values for the columns
    RETURNS:
        lastrowid (int) OR False - the last ID for the transaction

    EXAMPLE: with [query]
        query = "INSERT INTO users (username,password,create_time) VALUES ("user_01", "user_01", "2022-03-15")"
        user_id = insertRow(db, query=query)

    EXAMPLE: with [query] and [col_values]
        user_id = insertRow(db,
                            query=INSERT INTO users (username,password,create_time) VALUES (?, ?, ?),
                            col_values=["user_01", "user_01", "2022-03-15"])

    EXAMPLE: with [params] directly
        user_id = insertRow(db,
                            table="users",
                            columns=["username", "password", "create_time"],
                            col_values=["user_01", "user_01", "2022-03-15"])

    EXAMPLE: with [params] as (dict)
        params = {
            "table": "users",
            "columns": ["username", "password", "create_time"],
            "col_values": [username, password, create_time],
        }
        user_id = insertRow(db, **params)
    """
    if query:
        col_values = kwargs.get("col_values")
    else:
        table      = kwargs["table"]
        columns    = kwargs["columns"]
        col_values = kwargs["col_values"]
        query = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({', '.join(['?']*len(columns))});"
    print(query)
    if col_values:
        print(" "*query.find("?"), col_values)

    try:
        cur = db.execute(query, col_values) if col_values else db.execute(query)
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"ProgrammingError": e.args, "query": query, "col_values": col_values}

    if cur:
        return cur.lastrowid
    return False

###############################################################################
#                               READ OPERATIONS                               #
###############################################################################
def fetchRow(db, query="", **kwargs):
    """
    Fetch a single row from a table in the database

    ARGS:
        Required - db (object)          - the database connection object
        Optional - query (str)          - a complete SQL query

        Required - table (str)          - the table to fetch data from
        Optional - columns (list)       - columns to filter by
        Optional - where (str)          - conditional "WHERE" statement
        Optional - values (str|list)    - the value(s) for the "WHERE" statement
    RETURNS:
        row (dict) OR False - the row data as a (dict) object

    EXAMPLE: with [query]
        row = fetchRow(db, query="SELECT * FROM users;")

    EXAMPLE: with [query] and [values]
        row = fetchRow(db, query="SELECT * FROM users WHERE (user_id=?);", values=["5"])

    EXAMPLE: with [params] directly
        row = fetchRow(db, table="users", where="user_id=?", values="5")

    EXAMPLE: with [params] as (dict)
        user_id = "5"
        params = {
            "table": "users",
            "where": "user_id=?",
            "values": user_id
        }
        row = fetchRow(db, **params)
    """
    if query:
        values = [kwargs.get("values")] if isinstance(kwargs.get("values"), str) else kwargs.get("values")
    else:
        table     = kwargs.get("table")
        columns   = "*" if not kwargs.get("columns") else ",".join(kwargs["columns"])
        condition = "1" if not kwargs.get("where") else f'({kwargs["where"]})'
        values    = [kwargs.get("values")] if isinstance(kwargs.get("values"), str) else kwargs.get("values")
        query = f"SELECT {columns} FROM {table} WHERE {condition};"
    print(query)
    if values:
        print(" "*query.find("?"), values)

    try:
        row = db.execute(query, values).fetchone() if values else db.execute(query).fetchone()
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"ProgrammingError": e.args, "query": query, "values": values}

    if row:
        return dict(row)
    return False

def fetchRows(db, query="", **kwargs):
    """
    Fetch multiple rows from a table in the database

    ARGS:
        Required - db (object)          - the database connection object
        Optional - query (str)          - a complete SQL query

        Required - table (str)          - the table to fetch data from
        Optional - columns (list)       - columns to filter by
        Optional - where (str)          - conditional "WHERE" statement
        Optional - values (str|list)    - the value(s) for the "WHERE" statement
    RETURNS:
        rows (list[(dict)]) OR False - the rows of data as a (list) of (dict) objects

    EXAMPLE: with [query]
        rows = fetchRows(db, query="SELECT * FROM users;")

    EXAMPLE: with [query] and [values]
        rows = fetchRows(db, query="SELECT * FROM users WHERE (user_id=?);", values=["5"])

    EXAMPLE: with [params] directly
        rows = fetchRows(db, table="users", where="user_id=?", values="5")

    EXAMPLE: with [params] as (dict)
        user_id = "5"
        params = {
            "table": "users",
            "where": "user_id=?",
            "values": user_id
        }
        rows = fetchRows(db, **params)
    """
    if query:
        values = [kwargs.get("values")] if isinstance(kwargs.get("values"), str) else kwargs.get("values")
    else:
        table     = kwargs.get("table")
        columns   = "*" if not kwargs.get("columns") else ",".join(kwargs["columns"])
        condition = "1" if not kwargs.get("where") else f'({kwargs["where"]})'
        values    = [kwargs.get("values")] if isinstance(kwargs.get("values"), str) else kwargs.get("values")
        query = f"SELECT {columns} FROM {table} WHERE {condition};"
    print(query)
    if values:
        print(" "*query.find("?"), values)

    try:
        rows = db.execute(query, values).fetchall() if values else db.execute(query).fetchall()
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"ProgrammingError": e.args, "query": query, "values": values}

    if rows:
        if len(rows) == 1:
            return dict(rows[0])
        return [dict(row) for row in rows]
    return False

###############################################################################
#                              UPDATE OPERATIONS                              #
###############################################################################
def updateRow(db, query="", **kwargs):
    """
    Update data in the database

    ARGS:
        Required - db (object)          - the database connection object
        Optional - query (str)          - a complete SQL query

        Required - table (str)          - the table to update data
        Required - columns (list)       - the columns to edit
        Required - col_values (list)    - the values for the columns
        Required - where (str)          - conditional "WHERE" statement
        Required - values (str|list)    - the value(s) for the "WHERE" statement
    RETURNS:
        num_edits (int) OR False - the number of rows that were edited

    EXAMPLE: with [query]
        num_edits = updateRow(db, query="UPDATE users SET username=? WHERE (user_id=6);")

    EXAMPLE: with [query] and [col_values] and [values]
        num_edits = updateRow(db,
                                query="UPDATE users SET username=? WHERE (user_id=?);",
                                col_values=["user_06"], values=["6"])

    EXAMPLE: with [params] directly
        num_edits = updateRow(db,
                                table="users",
                                columns=["username"],
                                col_values=["user_06"],
                                where="user_id=?",
                                values=["6"])

    EXAMPLE: with [params] as (dict)
        username = "user_06"
        params = {
            "table": "users",
            "columns": ["username"],
            "col_values": [username],
            "where": "user_id=?",
            "values": [username],
        }
        num_edits = updateRow(db, **params)
    """
    if query:
        col_values = kwargs.get("col_values")
        values     = [kwargs.get("values")] if isinstance(kwargs.get("values"), str) else kwargs.get("values")
    else:
        table      = kwargs.get("table")
        # columns    = ", ".join([f"{col}=?" for col in kwargs["columns"]])
        # col_values = kwargs["col_values"]
        columns, col_values = parseColumnValues(kwargs["columns"], kwargs["col_values"])
        condition  = f'({kwargs["where"]})'
        values     = [kwargs["values"]] if isinstance(kwargs["values"], str) else kwargs["values"]
        query = f"UPDATE {table} SET {columns} WHERE {condition};"
    print(query)
    print(" "*query.find("?"), col_values, values)

    try:
        cur = db.execute(query, col_values+values) if (col_values or values) else db.execute(query)
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"ProgrammingError": e.args, "query": query, "col_values": col_values, "values": values}

    return cur.rowcount

###############################################################################
#                              DELETE OPERATIONS                              #
###############################################################################
def deleteRow(db, query="", **kwargs):
    """
    Delete row(s) from the database

    ARGS:
        Required - db (object)          - the database connection object
        Optional - query (str)          - a complete SQL query
        Required - table (str)          - the table to delete data from
        Required - where (str)          - conditional "WHERE" statement
        Required - values (str|list)    - the value(s) for the "WHERE" statement
    RETURNS:
        num_delets (int) OR False - the number of rows that were deleted

    EXAMPLE: with [query]
        num_deletes = deleteRow(db, query="DELETE FROM users WHERE (user_id=6);")

    EXAMPLE: with [query] and [values]
        num_deletes = deleteRow(db, query="DELETE FROM users WHERE (user_id=?);", values=["6"])

    EXAMPLE: with [params] directly
        num_deletes = deleteRow(db,
                                table="users",
                                where="user_id=?",
                                col_values=["6"])

    EXAMPLE: with [params] as (dict)
        user_id = 6
        params = {
            "table": "users",
            "where": "user_id=?",
            "values": user_id,
        }
        num_deletes = deleteRow(db, **params)
    """
    if query:
        values = [kwargs["values"]] if isinstance(kwargs["values"], str) else kwargs["values"]
    else:
        table      = kwargs.get("table")
        condition  = f'({kwargs["where"]})'
        values     = [kwargs["values"]] if isinstance(kwargs["values"], str) else kwargs["values"]
        query = f"DELETE FROM {table} WHERE {condition};"
    print(query)
    print(" "*query.find("?"), values)

    try:
        cur = db.execute(query, values)
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"ProgrammingError": e.args, "query": query, "values": values}

    return cur.rowcount

###############################################################################
#                               Helper Functions                              #
###############################################################################

# Utility Functions ###########################################################
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

# Parsers #####################################################################
def parseFilters(filters, conditions):
    filter_conditions = ""
    filter_values = []
    regex = r'''
        (?P<col>[a-zA-Z0-9_-]+) |                        # -- match column name
        (?P<op>[!<>=]+) |                                # -- match operator (>, <, =, ==, !=, >=, <=, <>)
        (?P<dt>(\"|\')([0-9a-zA-Z@_\-\ \:\.]+)(\"|\')) | # -- match "value" (datetime, integer, double)
        \s+(?P<exp>(AND|OR))\s                           # -- match logical (AND, OR)
    '''
    r = re.compile(regex, re.VERBOSE)
    for match in r.finditer(filters):
        m = match.groupdict()
        for k, v in m.items():
            if v:
                if k == "col":
                    filter_conditions += f"{v}"
                elif k == "op":
                    filter_conditions += f" {v} ?"
                elif k == "exp":
                    filter_conditions += f" {v} "
                else:
                    filter_values.append(v.strip('"').strip("'"))
    filter_conditions = filter_conditions.strip()
    print(f'filter_conditions: {filter_conditions}')
    print(f'filter_values: {filter_values}')

    if conditions:
        filter_conditions = f' AND {filter_conditions}'
    else:
        filter_conditions = filter_conditions
    return filter_conditions, filter_values

def parseColumnValues(cols, vals):
    columns = ""
    col_values = []
    # -- check for expressions containing "column name"
    for i, expression in enumerate([any([col in val for col in cols]) for val in vals]):
        if expression:
            columns += f"{cols[i]}={vals[i]}, "
        else:
            columns += f"{cols[i]}=?, "
            col_values.append(vals[i])
    columns = columns.strip(", ")

    print(f"columns: '{columns}'")
    print(f"col_values: {col_values}")
    return columns, col_values

# Logging #####################################################################
# -- https://stackoverflow.com/questions/31080214/python-bottle-always-logs-to-console-no-logging-to-file
def getLogger():
    logger = logging.getLogger('m2band.py')

    logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler('m2band.log')
    formatter = logging.Formatter('%(msg)s')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def log_to_logger(fn):
    '''
    Wrap a Bottle request so that a log line is emitted after it's handled.
    (This decorator can be extended to take the desired logger as a param.)
    '''
    @wraps(fn)
    def _log_to_logger(*args, **kwargs):
        request_time = datetime.now()
        actual_response = fn(*args, **kwargs)
        ip_address = (
            request.environ.get('HTTP_X_FORWARDED_FOR')
            or request.environ.get('REMOTE_ADDR')
            or request.remote_addr
        )
        logger.info('%s %s %s %s %s' % (ip_address,
                                        request_time,
                                        request.method,
                                        request.url,
                                        response.status))
        if isinstance(actual_response, dict):
            if not actual_response.get("message") == "available commands":
                logger.info(json.dumps(actual_response, default=str, indent=2))
        else:
            logger.info(actual_response)
        return actual_response
    return _log_to_logger

logger = getLogger()
