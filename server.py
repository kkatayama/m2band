# from bottle import hook, install, route, run, request, response, redirect, static_file, urlencode, HTTPError
from bottle import hook, route, run, request, redirect, urlencode
from bottle_sqlite import SQLitePlugin, sqlite3
# from bottle_errorsrest import ErrorsRestPlugin
# from datetime import datetime
from db_functions import (
    insertRow, fetchRow, fetchRows, updateRow, deleteRow,
    addTable, deleteTable, getTable, getTables, getColumns,
    securePassword, checkPassword, checkUserAgent, clean2,
    clean, extract, mapUrlPaths, getLogger, log_to_logger, logger,
    parseURI, parseUrlPaths, parseFilters, parseColumnValues,
    ErrorsRestPlugin
)
from rich import print
from docs.usage import (
    usage_add, usage_get, usage_edit, usage_delete,
    usage_create_table, usage_delete_table,
    usage_login, usage_logout
)
import bottle
import json
import os
import re


# app = Bottle()
app = bottle.app()
plugin = SQLitePlugin(dbfile="m2band.db", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
app.install(plugin)
app.install(log_to_logger)
app.install(ErrorsRestPlugin())

# -- hook to strip trailing slash
@hook('before_request')
def strip_path():
    request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')

# -- index - response: available commands
@route("/", method=["GET", "POST", "PUT", "DELETE"])
def index():
    res = {
        "message": "available commands",
        "Core_Functions": {
            "/add": usage_add, "/get": usage_get, "/edit": usage_edit, "/delete": usage_delete,
        },
        "Admin_Functions": {
            "/createTable": usage_create_table, "/deleteTable": usage_delete_table,
        },
        "User_Functions": {
            "/login": usage_login, "/logout": usage_logout,
        },
    }
    return clean(res)

###############################################################################
#                   Core Function /add - Add Data to a Table                  #
###############################################################################
@route("/add", method=["GET", "POST", "PUT", "DELETE"])
@route("/add/<table_name>", method=["GET", "POST", "PUT", "DELETE"])
@route("/add/<table_name>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def add(db, table_name="", url_paths=""):
    if table_name == 'usage':
        return usage_add

    tables = getTables(db)
    table = getTable(db, tables, table_name)
    if not table:
        return clean({"message": "active tables in the database", "tables": tables})

    # -- parse "params" and "filters" from HTTP request
    required_columns = getColumns(db, table, required=True)
    params, filters = parseUrlPaths(url_paths, request.params, required_columns)

    # -- check for required parameters
    missing_keys = (params.keys() ^ required_columns.keys())
    missing_params = {k: table["columns"][k] for k in required_columns if k in missing_keys}
    if missing_params:
        res = {"message": "missing paramaters", "required": [required_columns],
               "missing": [missing_params], "submitted": [params]}
        return clean(res)

    # -- the users table requires additional formatting and checking
    if table_name == "users":
        params.update({"password": securePassword(params["password"])})
        if fetchRow(db, table=table, where="username=?", values=params["username"]):
            res = {"message": "user exists", "username": params["username"]}
            return clean(res)

    # -- define "columns" to edit and "values" to insert
    edit_items = {k: params[k] for k in required_columns if params.get(k)}
    columns, col_values = list(edit_items.keys()), list(edit_items.values())

    # -- query database -- INSERT INTO oximeter (user_id,heart_rate,...) VALUES (?, ?, ...);
    col_id = insertRow(db, table=table, columns=columns, col_values=col_values)
    if isinstance(col_id, dict):
        if col_id.get('Error'):
            return clean(col_id)

    # -- send response message
    col_ref = getColumns(db, table, ref=True)  # -- get (.*_id) name for table
    res = {"message": f"data added to <{table_name}>", col_ref: col_id}
    for r in re.findall(r"(.*_id)", " ".join(required_columns)):
        res[r] = params.get(r)
    return clean(res)

###############################################################################
#                 Core Function /get - Fetch Data From a Table                #
###############################################################################
@route("/get", method=["GET", "POST", "PUT", "DELETE"])
@route("/get/<table_name>", method=["GET", "POST", "PUT", "DELETE"])
@route("/get/<table_name>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def get(db, table_name="", url_paths=""):
    print(f"request.params = {dict(request.params)}")
    if table_name == 'usage':
        return usage_get

    tables = getTables(db)
    table = getTable(db, tables, table_name)
    if not table:
        return clean({"message": "active tables in the database", "tables": tables})

    # -- parse "params" and "filters" from HTTP request
    params, filters = parseUrlPaths(url_paths, request.params, table["columns"])

    # -- build "conditions" string and "values" array for "fetchRows()"
    conditions = " AND ".join([f"{param}=?" for param in params.keys()])
    values = list(params.values())
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database -- SELECT * FROM users WHERE (user_id=?);
    rows = fetchRows(db, table=table, where=conditions, values=values)
    if isinstance(rows, dict):
        if rows.get('Error'):
            return clean(rows)
        message = f"1 {table_name.rstrip('s')} entry found"
    elif isinstance(rows, list):
        message = f"found {len(rows)} {table_name.rstrip('s')} entries"
    else:
        message = f"0 {table_name.rstrip('s')} entries found using submitted parameters"
        rows = {"submitted": [params] + [{"filter": filters}]}

    # -- send response message
    res = {"message": message, "data": rows}
    return clean(res)

###############################################################################
#                  Core Function /edit - Edit Data in a Table                 #
###############################################################################
@route("/edit", method=["GET", "POST", "PUT", "DELETE"])
@route("/edit/<table_name>", method=["GET", "POST", "PUT", "DELETE"])
@route("/edit/<table_name>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def edit(db, table_name="", url_paths=""):
    print(f"request.params = {dict(request.params)}")
    if table_name == 'usage':
        return usage_edit

    tables = getTables(db)
    table = getTable(db, tables, table_name)
    if not table:
        return clean({"message": "active tables in the database", "tables": tables})

    # -- parse "params" and "filters" from HTTP request
    editable_columns = getColumns(db, table, editable=True)
    non_edit_columns = getColumns(db, table, non_editable=True)
    params, filters = parseUrlPaths(url_paths, request.params, table["columns"])
    print(f"params = {params}\nfilters = '{filters}'")

    # -- the users table requires additional formatting and checking
    if (table_name == "users") and params.get("password"):
        params.update({"password": securePassword(params["password"])})

    # -- at least 1 edit parameter required
    if not (editable_columns.keys() & params.keys()):
        submitted = {**{"filter": filters}, **params} if filters else params
        res = {"message": "missing a parameter to edit", "editable": [editable_columns],
               "submitted": [submitted]}
        return clean(res)

    # -- at least 1 query parameter required
    # TODO: add try except for (submitted)
    submitted = {**{"filter": filters}, **params} if filters else params
    query_params = {**non_edit_columns, **{"filter": filters}}
    if not (submitted.keys() & query_params.keys()):
        res = {"message": "missing a query parameter", "query_params": [query_params], "submitted": [submitted]}
        return clean(res)

    # -- define "columns" to edit and "values" to insert (parsed from params in HTTP request)
    edit_items = {k: params[k] for k in editable_columns if params.get(k)}
    columns, col_values = list(edit_items.keys()), list(edit_items.values())

    # -- build "conditions" string and "values" string/array for "updateRow()"
    conditions = " AND ".join([f"{param}=?" for param in non_edit_columns if params.get(param)])
    values = [params[param] for param in non_edit_columns if params.get(param)]
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database -- UPDATE users SET username=? WHERE (user_id=?);
    args = {
        "table": table, "columns": columns, "col_values": col_values,
        "where": conditions, "values": values
    }
    num_edits = updateRow(db, **args)
    if isinstance(num_edits, dict):
        if num_edits.get('Error'):
            return clean(num_edits)
    elif num_edits:
        if num_edits == 1:
            message = f"edited 1 {table_name.rstrip('s')} entry"
        else:
            message = f"edited {num_edits} {table_name.rstrip('s')} entries"
    else:
        message = f"0 {table_name.rstrip('s')} entries found matching your parameters"

    # -- send response message
    res = {"message": message, "submitted": [submitted]}
    return clean(res)

###############################################################################
#             Core Function /delete - Delete Data from a Table                #
###############################################################################
@route("/delete", method=["GET", "POST", "PUT", "DELETE"])
@route("/delete/<table_name>", method=["GET", "POST", "PUT", "DELETE"])
@route("/delete/<table_name>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def delete(db, table_name="", url_paths=""):
    print(f"request.params = {dict(request.params)}")
    if table_name == 'usage':
        return usage_delete

    tables = getTables(db)
    table = getTable(db, tables, table_name)
    if not table:
        return clean({"message": "active tables in the database", "tables": tables})

    # -- parse "params" and "filters" from HTTP request
    params, filters = parseUrlPaths(url_paths, request.params, table["columns"])
    print(f"params = {params}\nfilters = '{filters}'")

    # -- to prevent accidental deletion of everything, at least 1 parameter is required
    submitted = {**{"filter": filters}, **params} if filters else params
    query_params = {**table["columns"], **{"filter": filters}}
    if not (submitted.keys() & query_params.keys()):
        res = {"message": "missing a query param(s)", "query_params": [query_params], "submitted": [submitted]}
        return clean(res)

    # -- build "conditions" string and "values" string/array for "updateRow()"
    conditions = " AND ".join([f"{param}=?" for param in table["columns"] if params.get(param)])
    values = [params[param] for param in table["columns"] if params.get(param)]
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database -- DELETE FROM users WHERE (user_id=?);
    num_deletes = deleteRow(db, table=table, where=conditions, values=values)
    if isinstance(num_deletes, dict):
        if num_deletes.get('Error'):
            return clean(num_deletes)
    elif num_deletes:
        if num_deletes == 1:
            message = f"1 {table_name.rstrip('s')} entry deleted"
        else:
            message = f"{num_deletes} {table_name.rstrip('s')} entries deleted"
    else:
        message = f"0 {table_name.rstrip('s')} entries found matching your parameters"

    # -- send response message
    res = {"message": message, "submitted": [submitted]}
    return clean(res)

###############################################################################
#                      User's Table: Additional Functions                     #
###############################################################################
@route("/login", method=["GET", "POST", "PUT", "DELETE"])
@route("/login/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def login(db, url_paths=""):
    # -- parse "params" and "filters" from HTTP request
    table = getTable(db, table_name="users")
    required_columns = getColumns(db, table, required=True)
    params, filters = parseUrlPaths(url_paths, request.params, required_columns)
    print(f"params = {params}\nfilters = '{filters}'")

    # -- check for required parameters
    if any(k not in params.keys() for k in required_columns):
        res = {"message": "missing parameters", "required": [required_columns], "submitted": [params]}
        return clean(res)

    # -- check if user exists
    row = fetchRow(db, table="users", where="username=?", values=params["username"])
    if not row:
        res = {"message": "user does not exist", "username": params["username"]}
        return clean(res)

    # -- check user submitted password against the one retrieved from the database
    if not checkPassword(params["password"], row["password"]):
        res = {"message": "incorrect password", "password": params["password"]}
        return clean(res)

    # -- send response message
    res = {"message": "user login success", "user_id": row["user_id"], "username": row["username"]}
    return clean(res)

@route("/logout", method=["GET", "POST", "PUT", "DELETE"])
def logout(db):
    # response.delete_cookie("user_id")

    # -- send response message
    res = {"message": "user logged out"}
    return clean(res)

###############################################################################
#                          Database Admin Functions                           #
###############################################################################
@route("/createTable")
@route("/createTable/<table_name>")
@route("/createTable/<table_name>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def createTable(db, table_name="", url_paths=""):
    required_columns = {"user_id": "INTEGER", "{ref}_id": "INTEGER", "{ref}_time": "DATETIME",
                        "column_name": "column_type",
                        "available_types": ["INTEGER", "DOUBLE", "TEXT", "DATETIME"]}
    if table_name == 'usage':
        return usage_create_table
    if (not table_name):
        return clean({"message": "active tables in the database", "tables": getTables(db)})
    if ((not url_paths) and (not request.params)):
        res = {"message": "missing paramaters", "required": [required_columns],
               "available_types": ["INTEGER", "DOUBLE", "TEXT", "DATETIME"],
               "Exception": "\"{ref}_id\" not required when creating \"users\" table", "submitted": []}
        return clean(res)

    # -- parse "params" and "url_paths" from HTTP request
    params, columns = mapUrlPaths(url_paths, request.params, table_name)

    # if not checkCreateTable(params, columns):
    #     res = {"message": "missing paramaters", "required": [required_columns],
    #            "missing": [missing_params], "submitted": [params]}
    #     return clean(res)

    # -- CREATE TABLE <table>
    res = addTable(db, table=table_name, columns=columns)
    res.update({"table": table_name})
    return clean(res)

@route("/deleteTable")
@route("/deleteTable/<table_name>")
def dropTable(db, table_name=""):
    if table_name == 'usage':
        return usage_delete_table

    tables = getTables(db)
    table = getTable(db, tables, table_name)
    if not table:
        return clean({"message": "active tables in the database", "tables": tables})

    # -- DROP TABLE <table>
    res = deleteTable(db, table=table_name)
    res.update({"table": table_name})
    return clean(res)



###############################################################################
#                    Old Routes For Backwards Compatability                   #
###############################################################################
"""
These routes are here to keep existing apps working.
Eventually, they should be deleted.
Apps should migrate to the new Framework Format as these routes are currently using.
"""
# users table #################################################################
@route("/addUser", method=["GET", "POST", "PUT", "DELETE"])
@route("/createUser", method=["GET", "POST", "PUT", "DELETE"])
def addUser(db):
    print(f"request.url = {request.url}")
    return redirect(f'https://m2band.hopto.org/add/users?{urlencode(request.params)}')

@route("/getUser", method=["GET", "POST", "PUT", "DELETE"])
@route("/getUsers", method=["GET", "POST", "PUT", "DELETE"])
def getUserOld(db):
    print(f"request.url = {request.url}")
    return redirect(f'https://m2band.hopto.org/get/users?{urlencode(request.params)}')

@route("/editUser", method=["GET", "POST", "PUT", "DELETE"])
def editUser(db):
    print(f"request.url = {request.url}")
    return redirect(f'https://m2band.hopto.org/edit/users?{urlencode(request.params)}')

@route('/deleteUser', method=["GET", "POST", "PUT", "DELETE"])
def deleteUser(db):
    print(f"request.url = {request.url}")
    return redirect(f'https://m2band.hopto.org/delete/users?{urlencode(request.params)}')

# oximeter table ##############################################################
@route("/addSensorData", method=["GET", "POST", "PUT", "DELETE"])
def addSensorData(db):
    print(f"request.url = {request.url}")
    return redirect(f'https://m2band.hopto.org/add/oximeter?{urlencode(request.params)}')

@route("/getSensorData", method=["GET", "POST", "PUT", "DELETE"])
@route("/getAllSensorData", method=["GET", "POST", "PUT", "DELETE"])
def getSensorOld(db):
    print(f"request.url = {request.url}")
    return redirect(f'https://m2band.hopto.org/get/oximeter?{urlencode(request.params)}')

@route("/editSensorData", method=["GET", "POST", "PUT", "DELETE"])
def editSensorData(db):
    print(f"request.url = {request.url}")
    return redirect(f'https://m2band.hopto.org/edit/oximeter?{urlencode(request.params)}')

@route("/deleteSensorData", method=["GET", "POST", "PUT", "DELETE"])
def deleteSensorData(db):
    print(f"request.url = {request.url}")
    return redirect(f'https://m2band.hopto.org/delete/oximeter?{urlencode(request.params)}')


# -- Run Web Server
port = int(os.environ.get("PORT", 8080))
# run(host="0.0.0.0", port=port, reloader=True)
run(app, host="0.0.0.0", port=port, reloader=True)
