from bottle import Bottle, run, request, response, redirect, static_file
from bottle_sqlite import SQLitePlugin, sqlite3
from datetime import datetime
from db_functions import *
# from rich.traceback import install
# from rich import print, inspect, print_json, pretty
import json
import os

# pretty.install()

app = Bottle()
plugin = SQLitePlugin(dbfile="m2band.db", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
app.install(plugin)
app.install(log_to_logger)

@app.route("/", method=["GET", "POST", "PUT", "DELETE"])
def index():
    with open('all_commands.js') as f:
        res = json.load(f)
    return clean(res)

@app.route("/get", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/get/", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/get/<table>", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/get/<table>/", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/get/<table>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/get/<table>/<url_paths:path>/", method=["GET", "POST", "PUT", "DELETE"])
def get(db, table="", url_paths=""):
    print(request.url_args)
    if not table:
        return clean({"message": "available tables in the database", "tables": getTables(db)})
    if table == 'usage':
        res = {
            "message": "usage options",
            "/get/<table_name>": "returns all rows in a table",
            "/get/<table_name>/<column_name>/<column_value>/../..": "query rows matching [name='value', ...]",
            "/get/<table_name>/filter/<filter_string>": "query rows with filter (create_time > '2022-03-30')",
            "/get/<table_name>/<column_name>/<column_value>/../filter/<filter_string>": "use query and filter"
        }
        return clean(res)

    # -- parse "params" and "filters" from HTTP request
    all_columns = getColumns(db, table)
    params, filters = parseUrlPaths(url_paths, request.params, all_columns)

    # -- build "conditions" string and "values" array for "fetchRows()"
    conditions = " AND ".join([f"{param}=?" for param in params.keys()])
    values     = list(params.values())
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database -- SELECT * FROM users WHERE (user_id=?);
    rows = fetchRows(db, table=table, where=conditions, values=values)
    if isinstance(rows, dict):
        if rows.get('Error'):
            return clean(rows)
        message = f"1 {table.rstrip('s')} entry found"
    elif isinstance(rows, list):
        message = f"found {len(rows)} {table.rstrip('s')} entries"
    else:
        message = f"no {table.rstrip('s')} data found"
        rows = {"your_params": request.params}

    # -- send response message
    res = {"message": message, "data": clean(rows)}
    return clean(res)

###############################################################################
#                      User's Table: Additional Functions                     #
###############################################################################
@app.route("/login", method=["GET", "POST", "PUT", "DELETE"])
def login(db):
    table = "users"

    # -- parse "params" from HTTP request
    required_columns = getColumns(db, table, required=True)
    params = {k:v for (k,v) in request.params.items() if k in required_columns}

    # -- check for required parameters
    if any(k not in params.keys() for k in required_columns):
        res = {"message": "missing parameters", "required": required_columns, "supplied": request.params}
        return clean(res)

    # -- check if user exists
    row = fetchRow(db, table=table, where="username=?", values=params["username"])
    if not row:
        res = {"message": "user does not exist", "username": params["username"]}
        return clean(res)

    # -- check user supplied password against the one retrieved from the database
    if not checkPassword(params["password"], row["password"]):
        res = {"message": "incorrect password", "password": params["password"]}
        return clean(res)

    # -- send response message
    res = {"message": "user login success", "user_id": row["user_id"], "username": row["username"]}
    return clean(res)

@app.route("/logout", method=["GET", "POST", "PUT", "DELETE"])
def logout(db):
    # response.delete_cookie("user_id")

    # -- send response message
    res = {"message": "user logged out"}
    return clean(res)

###############################################################################
#                         User's Table: Core Functions                        #
###############################################################################
@app.route("/addUser", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/createUser", method=["GET", "POST", "PUT", "DELETE"])
def addUser(db):
    table = "users"

    # -- parse "params" from HTTP request
    required_columns  = getColumns(db, table, required=True)
    params = {k:v for (k,v) in request.params.items() if k in required_columns}

    # -- check for required parameters
    if any(k not in params.keys() for k in required_columns):
        res = {"message": "missing paramaters", "required": required_columns, "supplied": request.params}
        return clean(res)

    # -- update params to include encrypted "password"
    params.update({"password": securePassword(params["password"])})

    # -- check if user exists ####################################################
    if fetchRow(db, table=table, where="username=?", values=params["username"]):
        res = {"message": "user exists", "username": params["username"]}
        return clean(res)

    # If user doesn't exist, create user ######################################
    # -- define "columns" to edit and "col_values" to insert
    columns    = [column for column in required_columns if params.get(column)]
    col_values = [params[column] for column in columns]

    # -- query database -- INSERT INTO users (username,password,create_time) VALUES (?, ?, ?);
    user_id = insertRow(db, table=table, columns=columns, col_values=col_values)
    if isinstance(user_id, dict):
        if user_id.get('Error'):
            return clean(user_id)

    # -- send response message
    res = {"message": "user created", "user_id": user_id, "username": params["username"]}
    return clean(res)

@app.route("/getUser", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/getUsers", method=["GET", "POST", "PUT", "DELETE"])
def getUser(db):
    table = "users"

    # -- parse "parameters" and "filters" from HTTP request
    filters     = request.params.get("filter")
    all_columns = getColumns(db, table)
    params = {k:v for (k,v) in request.params.items() if k in all_columns}

    # -- build "conditions" string and "values" array for "fetchRows()"
    conditions = " AND ".join([f"{param}=?" for param in params.keys()])
    values     = list(params.values())
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database -- SELECT * FROM users WHERE (user_id=?);
    rows = fetchRows(db, table=table, where=conditions, values=values)
    if isinstance(rows, dict):
        if rows.get('Error'):
            return clean(rows)
        message = f"found 1 user"
    elif isinstance(rows, list):
        message = f"found {len(rows)} users"
    else:
        message = "found 0 users"
        rows = {"your_params": request.params}

    # -- send response message
    res = {"message": message, "data": clean(rows)}
    return clean(res)


@app.route("/editUser", method=["GET", "POST", "PUT", "DELETE"])
def editUser(db):
    table = "users"

    # -- parse "parameters" and "filters" from HTTP request
    filters     = request.params.get("filter")
    all_columns = getColumns(db, table)
    editable_columns = getColumns(db, table, all_columns, required=True)
    non_edit_columns = getColumns(db, table, all_columns, non_editable=True)
    params = {k:v for (k,v) in request.params.items() if k in all_columns}

    # -- if "password" is supplied, update params with encrypted "password"
    if params.get("password"):
        params.update({"password": securePassword(params["password"])})

    # -- at least 1 edit parameter required
    if not any(k in params.keys() for k in editable_columns):
        res = {"message": "missing edit parameter", "editable": editable_columns, "supplied": request.params}
        return clean(res)

    # -- at least 1 query parameter required
    query_params = non_edit_columns + ["filter"]
    if not any(k in params.keys() for k in query_params):
        res = {"message": "missing query parameter", "query_params": query_params, "supplied": request.params}
        return clean(res)

    # -- define "columns" to edit and "values" to insert (parsed from params in HTTP request)
    columns    = [column for column in editable_columns if params.get(column)]
    col_values = [params[column] for column in columns]

    # -- build "conditions" string and "values" string/array for "updateRow()"
    conditions = " AND ".join([f"{param}=?" for param in non_edit_columns if params.get(param)])
    values     = [params[param] for param in non_edit_columns if params.get(param)]
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database -- UPDATE users SET username=? WHERE (user_id=?);
    args = {
        "table": table,
        "columns": columns,
        "col_values": col_values,
        "where": conditions,
        "values": values
    }
    num_edits = updateRow(db, **args)
    if isinstance(num_edits, dict):
        if num_edits.get('Error'):
            return clean(num_edits)
    elif num_edits:
        if num_edits == 1:
            message = f"edited 1 {table.rstrip('s')} entry"
        else:
            message = f"edited {num_edits} {table.rstrip('s')} entries"
    else:
        message = f"0 {table.rstrip('s')} entries found matching your parameters"

    # -- send response message
    res = {"message": message, "supplied": request.params}
    return clean(res)

@app.route('/deleteUser', method=["GET", "POST", "PUT", "DELETE"])
def deleteUser(db):
    table = "users"

    # -- parse "params" and "filters" from HTTP request
    filters     = request.params.get("filter")
    all_columns = getColumns(db, table)
    params = {k:v for (k,v) in request.params.items() if k in all_columns}

    # -- to prevent accidental deletion of everything, at least 1 parameter is required
    query_params = all_columns + ["filter"]
    if not any(k in params.keys() for k in query_params):
        res = {"message": "missing query paramater", "query_params": query_params, "supplied": request.params}
        return clean(res)

    # -- build "conditions" string and "values" string/array for "deleteRow()"
    conditions = " AND ".join([f"{param}=?" for param in all_columns if params.get(param)])
    values     = [params[param] for param in all_columns if params.get(param)]
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database -- DELETE FROM users WHERE (user_id=?);
    num_deletes = deleteRow(db, table=table, where=conditions, values=values)
    if isinstance(num_deletes, dict):
        if num_deletes.get('Error'):
            return clean(num_deletes)
    elif num_deletes:
        if num_deletes == 1:
            message = f"1 {table.rstrip('s')} entry deleted"
        else:
            message = f"{num_deletes} {table.rstrip('s')} entries deleted"
    else:
        message = f"0 {table.rstrip('s')} entries found matching your parameters"

    # -- send response message
    res = {"message": message, "supplied": request.params}
    return clean(res)

###############################################################################
#                        Oximeter Table: Core Functions                       #
###############################################################################
@app.route("/addSensorData", method=["GET", "POST", "PUT", "DELETE"])
def addSensorData(db):
    table = "oximeter"

    # -- parse "parameters" from HTTP request
    required_columns = getColumns(db, table, required=True)
    params = {k:v for (k,v) in request.params.items() if k in required_columns}

    # -- check for required parameters
    if any(k not in params.keys() for k in required_columns):
        res = {"message": "missing paramaters", "required": required_columns, "supplied": request.params}
        return clean(res)

    # -- define "columns" to edit and "values" to insert
    columns    = [column for column in required_columns if params.get(column)]
    col_values = [params[column] for column in columns]

    # -- query database -- INSERT INTO oximeter (user_id,heart_rate,...) VALUES (?, ?, ...);
    col_id = insertRow(db, table=table, columns=columns, col_values=col_values)
    if isinstance(col_id, dict):
        if col_id.get('Error'):
            return clean(col_id)

    # -- send response message
    col_ref = getColumns(db, table, ref=True)  # -- get (.*_id) name for table
    res = {"message": f"data added to <{table}>", "user_id": user_id, col_ref: col_id}
    return clean(res)

@app.route("/getSensorData", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/getAllSensorData", method=["GET", "POST", "PUT", "DELETE"])
def getSensorData(db):
    table = "oximeter"

    # -- parse "parameters" and "filters" from HTTP request
    filters     = request.params.get("filter")
    all_columns = getColumns(db, table)
    params  = {k:v for (k,v) in request.params.items() if k in all_columns}

    # -- build "conditions" string and "values" array for "fetchRows()"
    conditions = " AND ".join([f"{param}=?" for param in params.keys()])
    values     = list(params.values())
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database
    rows = fetchRows(db, table=table, where=conditions, values=values)
    if isinstance(rows, dict):
        if rows.get('Error'):
            return clean(rows)
        message = f"found 1 entry"
    elif isinstance(rows, list):
        message = f"found {len(rows)} entries"
    else:
        message = "found 0 entries"
        rows = {"your_params": request.params}

    # -- send response message
    res = {"message": message, "data": rows}
    return clean(res)

@app.route("/editSensorData", method=["GET", "POST", "PUT", "DELETE"])
def editSensorData(db):
    table = "oximeter"

    # required_columns  = ["user_id"]
    # editable_columns = ["heart_rate", "blood_o2", "temperature"]
    # params_options = ["user_id", "heart_rate", "blood_o2", "temperature"]
    # filter_options = ["filter"]

    # -- parse "parameters" and "filters" from HTTP request
    filters     = request.params.get("filter")
    all_columns = getColumns(db, table)
    editable_columns = getColumns(db, table, all_columns, required=True)
    non_edit_columns = getColumns(db, table, all_columns, non_editable=True)
    params = {k:v for (k,v) in request.params.items() if k in all_columns}


    # -- at least 1 query parameter required
    query_params = non_edit_columns + ["filter"]
    if not any(k in params.keys() for k in query_params):
        res = {"message": "missing query parameter", "query_params": query_params, "supplied": request.params}
        return clean(res)

    # -- define "columns" to edit and "values" to insert (parsed from params in HTTP request)
    columns    = [column for column in editable_columns if params.get(column)]
    col_values = [params[column] for column in columns]

    # -- build "conditions" string and "values" string/array for "updateRow()"
    conditions = " AND ".join([f"{param}=?" for param in non_edit_columns if params.get(param)])
    values     = [params[param] for param in non_edit_columns if params.get(param)]
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database
    args = {
        "table": table,
        "columns": columns,
        "col_values": col_values,
        "where": conditions,
        "values": values
    }
    num_edits = updateRow(db, **args)
    if isinstance(num_edits, dict):
        if num_edits.get('Error'):
            return clean(num_edits)
    elif num_edits:
        if num_edits == 1:
            message = f"edited 1 {table.rstrip('s')} entry"
        else:
            message = f"edited {num_edits} {table.rstrip('s')} entries"
    else:
        message = f"0 {table.rstrip('s')} entries found matching your parameters"

    # -- send response message
    res = {"message": message, "supplied": request.params}
    return clean(res)

@app.route("/deleteSensorData", method=["GET", "POST", "PUT", "DELETE"])
def deleteSensorData(db):
    table = "oximeter"

    # -- parse "parameters" and "filters" from HTTP request
    filters     = request.params.get("filter")
    all_columns = getColumns(db, table)
    params = {k:v for (k,v) in request.params.items() if k in all_columns}

    # -- to prevent accidental deletion of everything, at least 1 parameter is required
    query_params = all_columns + ["filter"]
    if not any(k in params.keys() for k in query_params):
        res = {"message": "missing query paramater", "query_params": query_params, "supplied": request.params}
        return clean(res)

    # -- build "conditions" string and "values" string/array for "deleteRow()"
    conditions = " AND ".join([f"{param}=?" for param in all_columns if params.get(param)])
    values     = [params[param] for param in all_columns if params.get(param)]
    if filters:
        conditions, values = parseFilters(filters, conditions, values)

    # -- query database
    num_deletes = deleteRow(db, table=table, where=conditions, values=values)
    if isinstance(num_deletes, dict):
        if num_deletes.get('Error'):
            return clean(num_deletes)
    elif num_deletes:
        if num_deletes == 1:
            message = f"1 {table.rstrip('s')} entry deleted"
        else:
            message = f"{num_deletes} {table.rstrip('s')} entries deleted"
    else:
        message = f"0 {table.rstrip('s')} entries found matching your parameters"

    # -- send response message
    res = {"message": message, "supplied": request.params}
    return clean(res)


# -- Run Web Server
port = int(os.environ.get("PORT", 8080))
run(app, host="0.0.0.0", port=port, reloader=True)
