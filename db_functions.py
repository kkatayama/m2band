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
from bottle import request, response, FormsDict, template
from datetime import datetime
from functools import wraps
from pathlib import Path
from rich import print
from bs4 import BeautifulSoup
import subprocess
import logging
import sqlite3
import hashlib
import codecs
import time
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
        # table      = kwargs["table"]
        table      = kwargs["table"]["name"] if isinstance(kwargs.get("table"), dict) else kwargs.get("table")
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
        return {"Error": e.args, "query": query, "col_values": col_values, "kwargs": kwargs}

    # if cur:
    return cur.lastrowid
    # return False

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
        # table     = kwargs.get("table")
        table     = kwargs["table"]["name"] if isinstance(kwargs.get("table"), dict) else kwargs.get("table")
        columns   = "*" if not kwargs.get("columns") else ",".join(kwargs["columns"])
        # condition = "1" if not kwargs.get("where") else f'({kwargs["where"]})'
        condition = "1" if not kwargs.get("where") else f'{kwargs["where"]}'
        values    = [kwargs.get("values")] if isinstance(kwargs.get("values"), str) else kwargs.get("values")
        query = f"SELECT {columns} FROM {table} WHERE {condition};"

        # if condition:
        #     query = f"SELECT {columns} FROM {table} WHERE {condition};"
        # else:
        #     query = f"SELECT {columns} FROM {table};"
    print({'kwargs': kwargs})

    print(query)
    if values:
        print(" "*query.find("?"), values)

    try:
        row = db.execute(query, values).fetchone() if values else db.execute(query).fetchone()
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"Error": e.args, "query": query, "values": values, "kwargs": kwargs}

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

        Optional - force (bool)         - force return type list
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
        table     = kwargs["table"]["name"] if isinstance(kwargs.get("table"), dict) else kwargs.get("table")
        columns   = "*" if not kwargs.get("columns") else ",".join(kwargs["columns"])
        # condition = "1" if not kwargs.get("where") else f'({kwargs["where"]})'
        condition = "1" if not kwargs.get("where") else f'{kwargs["where"]}'
        values    = [kwargs.get("values")] if isinstance(kwargs.get("values"), str) else kwargs.get("values")

        # if condition:
        #     query = f"SELECT {columns} FROM {table} WHERE {condition};"
        # else:
        #     query = f"SELECT {columns} FROM {table};"
        query = f"SELECT {columns} FROM {table} WHERE {condition};"
    print({'kwargs': kwargs})
    print(query)
    if values:
        print(" "*query.find("?"), values)

    try:
        rows = db.execute(query, values).fetchall() if values else db.execute(query).fetchall()
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"Error": e.args, "query": query, "values": values, "kwargs": kwargs}

    if rows:
        if ((len(rows) == 1) and (not kwargs.get("force"))):
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
        table      = kwargs["table"]["name"] if isinstance(kwargs.get("table"), dict) else kwargs.get("table")
        # table      = kwargs.get("table")
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
        return {"Error": e.args, "query": query, "col_values": col_values, "values": values, "kwargs": kwargs}

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
        # table      = kwargs.get("table")
        table      = kwargs["table"]["name"] if isinstance(kwargs.get("table"), dict) else kwargs.get("table")
        condition  = f'({kwargs["where"]})'
        values     = [kwargs["values"]] if isinstance(kwargs["values"], str) else kwargs["values"]
        query = f"DELETE FROM {table} WHERE {condition};"
    print(query)
    print(" "*query.find("?"), values)

    try:
        cur = db.execute(query, values)
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"Error": e.args, "query": query, "values": values, "kwargs": kwargs}

    return cur.rowcount

###############################################################################
#                               Helper Functions                              #
###############################################################################
# DB Functions ################################################################
def addTable(db, query="", **kwargs):
    if not query:
        # table = kwargs.get("table")
        table = kwargs["table"]["name"] if isinstance(kwargs.get("table"), dict) else kwargs.get("table")
        columns = kwargs.get("columns")
        query = f'CREATE TABLE {table} ({", ".join(columns)});'
    print(query)
    try:
        cur = db.execute(query)
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"Error": e.args, "query": query, "values": values, "kwargs": kwargs}
    return {"message": f"{abs(cur.rowcount)} table created", "table": table, "columns": columns}

def deleteTable(db, query="", **kwargs):
    if not query:
        # table = kwargs.get("table")
        table = kwargs["table"]["name"] if isinstance(kwargs.get("table"), dict) else kwargs.get("table")
        query = f"DROP TABLE {table};"
    print(query)

    try:
        cur = db.execute(query)
    except (sqlite3.ProgrammingError, sqlite3.OperationalError) as e:
        print(e.args)
        return {"Error": e.args, "query": query, "values": values, "kwargs": kwargs}
    return {"message": f"{abs(cur.rowcount)} table deleted!"}

def getTable(db, tables=[], table_name=''):
    if not tables:
        tables = getTables(db)
    # table = next((filter(lambda t: t["name"] == table_name, tables)), None)
    table = dict(*filter(lambda t: t["name"] == table_name, tables))
    if table:
        table["columns"] = {c["name"]: c["type"].split()[0] for c in table["columns"]}
    return table

def getTables(db):
    args = {
        "table": 'sqlite_schema',
        # "columns": ["name", "type", "sql"],
        "columns": ["name", "type"],
        "where": "type = ? AND name NOT LIKE ?",
        "values": ['table', 'sqlite_%'],
        "force": True,
    }
    tables = fetchRows(db, **args)
    for table in tables:
        table["columns"] = getColumns(db, table)

    return tables

def getColumns(db, table, required=False, editable=False, non_editable=False, ref=False):
    if not table.get("columns"):
        query = f'PRAGMA table_info({table["name"]});'
        rows = db.execute(query).fetchall()
        col_info = []
        for row in [dict(row) for row in rows]:
            dflt = row["dflt_value"]
            info = {"name": row["name"], "type": f'{row["type"]} {"PRIMARY KEY" if row["pk"] else ""}'}
            info["type"] += f'{"NOT NULL"}' if row["notnull"] else ""
            info["type"] += f" DEFAULT ({dflt})" if dflt else ""
            col_info.append(info)
        return col_info

    regex = r"(_id|_time)" if table["name"] == "users" else r"((?<!user)_id|_time)"
    editable_columns = {key: table["columns"][key] for key in table["columns"] if not re.search(regex, key)}
    non_editable_columns = {key: table["columns"][key] for key in table["columns"] if re.search(regex, key)}

    if required or editable:
        return editable_columns
    if non_editable:
        return non_editable_columns
    if ref:
        return re.search(r"(.*_id)", " ".join(non_editable_columns)).group()
    return table["columns"]


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
    user_agent = request.environ["HTTP_USER_AGENT"] if request.environ.get("HTTP_USER_AGENT") else ""
    browser_agents = [
        "Mozilla",
        "Firefox",
        "Seamonkey",
        "Chrome",
        "Chromium",
        "Safari",
        "OPR",
        "Opera",
        "MSIE",
        "Trident",
    ]
    print(f'user_agent = {user_agent}')
    regex = r"({})".format("|".join(browser_agents))

    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, FormsDict):
                data.update({k: dict(v)})

    str_data = json.dumps(data, default=str, indent=2)
    if re.search(regex, user_agent):
        print(str_data)
        return template("templates/prettify.tpl", data=str_data)

    cleaned = json.loads(str_data)
    print(cleaned)
    return cleaned

# Parsers #####################################################################
# def extract(col_info, editable_columns):
#     return{k: v for k, v in {c.values() for c in col_info} if k in editable_columns}

def extract(info, cols):
    return{k: v for k, v in {c.values() for c in info} if k in cols}

def mapUrlPaths(url_paths, req_items, table=""):
    # dt = "DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'))"
    dt = "NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'))"
    r = re.compile(r"/", re.VERBOSE)
    keys = map(str.lower, r.split(url_paths)[::2])
    vals = map(str.upper, r.split(url_paths)[1::2])
    url_params = dict(zip(keys, vals))

    # -- process params
    req_params = {k.lower():v.upper() for (k,v) in req_items.items()}
    params = {**url_params, **req_params}

    # -- order and build columns for CREATE statement
    id_cols, time_cols, non_cols, rejects = ([] for i in range(4))
    for (k, v) in params.items():
        if re.match(r"([a-z_0-9]+_id)", k):
            if (table == "users") or ("user" not in k):
                id_cols.insert(0, f"{k} {v} PRIMARY KEY")
            else:
                id_cols.append(f"{k} {v} NOT NULL")
        elif re.match(r"([a-z_0-9]+_time)", k):
            time_cols.append(f"{k} {v} {dt}")
        elif re.match(r"([a-z_0-9]+)", k):
            non_cols.append(f"{k} {v} NOT NULL")
        else:
            reject.append({k: v})

    columns = id_cols + non_cols + time_cols
    print(f'params = {params}')
    print(f'columns = {columns}')
    return params, columns

def parseURI(url_paths):
    print(f'url_paths = {url_paths}')
    r = re.compile(r"/", re.VERBOSE)
    url_split = r.split(url_paths)

    if (len(url_split) % 2) == 0:
        p = map(str, url_split)
        url_params = dict(zip(p, p))
    elif url_paths:
        keys, values = ([] for i in range(2))
        for i in range(0, len(url_split), 2):
            if re.match(r"([a-z_]+)", url_split[i]):
                keys.append(url_split[i])
                values.append(url_split[i + 1])
            else:
                values[-1] = "/".join([values[-1], url_split[i]])
        url_params = dict(zip(keys, values))
    else:
        url_params = {}

    return url_params

def parseUrlPaths(url_paths, req_items, columns):
    # -- parse "params" and "filters" from url paths
    url_params = parseURI(url_paths)

    # -- process filters (pop from url_params if necessary)
    url_filters = url_params.pop("filter") if url_params.get("filter") else ""
    req_filters = req_items["filter"] if req_items.get("filter") else ""
    filters = " AND ".join([f for f in [url_filters, req_filters] if f])

    # -- process params
    req_params = {k:v for (k,v) in req_items.items() if k in columns}
    params = {**url_params, **req_params}

    return params, filters

def parseFilters(filters, conditions, values):
    regex = r"""
        ("|')(?P<val>[^"|^']*)("|')             # wrapped in single or double quotations
    """
    r = re.compile(regex, re.VERBOSE)
    f_conditions = r.sub("?", filters)

    filter_conditions = f_conditions if not conditions else " AND ".join([conditions, f_conditions])
    filter_values = values + [m.groupdict()["val"] for m in r.finditer(filters)]
    print(f'filter_conditions: "{filter_conditions}"')
    print(f'filter_values: {filter_values}')

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
                logger.info(json.dumps({"request.params": dict(request.params)}))
                logger.info(json.dumps(actual_response, default=str, indent=2))
        else:
            soup = BeautifulSoup(actual_response, 'html5lib')
            logger.info(json.dumps(json.loads(soup.select_one("pre").getText()), indent=2))
            # logger.info(json.dumps({'msg': }, default=str, indent=2))
            # logger.info(actual_response)
        return actual_response
    return _log_to_logger

logger = getLogger()

# DEPRECATED FUNCTIONS ########################################################
"""
def parseFilters(filters, conditions):
    filter_conditions = ""
    filter_values = []
    regex = r'''
        (?P<col>[a-z0-9_]+) |                        # -- match column name
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
"""
