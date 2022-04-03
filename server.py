from bottle import hook, install, route, run, request, response, redirect, static_file, urlencode
from bottle_sqlite import SQLitePlugin, sqlite3
from datetime import datetime
from db_functions import *
from rich import print, inspect
from docs.usage import *
import bottle
import json
import os


# app = Bottle()
app = bottle.app()
plugin = SQLitePlugin(dbfile="m2band.db", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
app.install(plugin)
app.install(log_to_logger)

# -- hook to strip trailing slash
@hook('before_request')
def strip_path():
    request.environ['PATH_INFO'] = request.environ['PATH_INFO'].rstrip('/')

# -- index - response: available commands
@route("/", method=["GET", "POST", "PUT", "DELETE"])
def index():
    # print(inspect(app, all=True))
    with open('docs/all_commands.json') as f:
        res = json.load(f)
    return clean(res)

###############################################################################
#                   Core Function /add - Add Data to a Table                  #
###############################################################################
@route("/add", method=["GET", "POST", "PUT", "DELETE"])
@route("/add/<table>", method=["GET", "POST", "PUT", "DELETE"])
@route("/add/<table>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def add(db, table="", url_paths=""):
    if table == 'usage':
        return usage_add
    if ((not table) or (table not in [t["name"] for t in getTables(db)])):
        return clean({"message": "active tables in the database", "tables": getTables(db)})

    # -- parse "params" and "filters" from HTTP request
    required_columns = getColumns(db, table, required=True)
    params, filters  = parseUrlPaths(url_paths, request.params, required_columns)

    # -- check for required parameters
    if any(k not in params.keys() for k in required_columns):
        res = {"message": "missing paramaters", "required": required_columns, "supplied": request.params}
        return clean(res)

    # -- the users table requires additional formatting and checking
    if table == "users":
        params.update({"password": securePassword(params["password"])})
        if fetchRow(db, table=table, where="username=?", values=params["username"]):
            res = {"message": "user exists", "username": params["username"]}
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
    res = {"message": f"data added to <{table}>", col_ref: col_id}
    for r in re.findall(r"(.*_id)", " ".join(required_columns)):
        res[r] = params.get(r)
    return clean(res)

###############################################################################
#                 Core Function /get - Fetch Data From a Table                #
###############################################################################
@route("/get", method=["GET", "POST", "PUT", "DELETE"])
@route("/get/<table>", method=["GET", "POST", "PUT", "DELETE"])
@route("/get/<table>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def get(db, table="", url_paths=""):
    print(f"request.params = {dict(request.params)}")
    if table == 'usage':
        return usage_get
    if ((not table) or (table not in [t["name"] for t in getTables(db)])):
        return clean({"message": "active tables in the database", "tables": getTables(db)})

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
        message = f"0 {table.rstrip('s')} entries found using supplied parameters"
        rows = {"supplied": request.params}

    # -- send response message
    res = {"message": message, "data": clean(rows)}
    return clean(res)

###############################################################################
#                  Core Function /edit - Edit Data in a Table                 #
###############################################################################
@route("/edit", method=["GET", "POST", "PUT", "DELETE"])
@route("/edit/<table>", method=["GET", "POST", "PUT", "DELETE"])
@route("/edit/<table>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def edit(db, table="", url_paths=""):
    print(f"request.params = {dict(request.params)}")
    if table == 'usage':
        return usage_edit
    if ((not table) or (table not in [t["name"] for t in getTables(db)])):
        return clean({"message": "active tables in the database", "tables": getTables(db)})

    # -- parse "params" and "filters" from HTTP request
    all_columns, col_info = getColumns(db, table, col=True)
    editable_columns = getColumns(db, table, all_columns, required=True)
    non_edit_columns = getColumns(db, table, all_columns, non_editable=True)
    params, filters  = parseUrlPaths(url_paths, request.params, all_columns)
    print(f"params = {params}\nfilters = '{filters}'")

    # -- the users table requires additional formatting and checking
    if (table == "users") and params.get("password"):
        params.update({"password": securePassword(params["password"])})

    # -- at least 1 edit parameter required
    if not any(k in params.keys() for k in editable_columns):
        res = {"message": "missing a parameter to edit",
               "editable": extract(col_info, editable_columns), "supplied": request.params}
        return clean(res)

    # -- at least 1 query parameter required
    # supplied = {'filter': filters} | params if filters else params
    supplied = {**{'filter': filters}, **params}
    query_params = non_edit_columns + ["filter"]
    if not any(k in supplied.keys() for k in query_params):
        res = {"message": "missing a query parameter",
               "query_params": extract(col_info, query_params), "supplied": supplied}
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
        "table": table, "columns": columns, "col_values": col_values,
        "where": conditions, "values": values
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
    res = {"message": message, "supplied": supplied}
    return clean(res)

###############################################################################
#             Core Function /delete - Delete Data from a Table                #
###############################################################################
@route("/delete", method=["GET", "POST", "PUT", "DELETE"])
@route("/delete/<table>", method=["GET", "POST", "PUT", "DELETE"])
@route("/delete/<table>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def edit(db, table="", url_paths=""):
    print(f"request.params = {dict(request.params)}")
    if table == 'usage':
        return usage_delete
    if ((not table) or (table not in [t["name"] for t in getTables(db)])):
        return clean({"message": "active tables in the database", "tables": getTables(db)})

    # -- parse "params" and "filters" from HTTP request
    all_columns = getColumns(db, table)
    params, filters  = parseUrlPaths(url_paths, request.params, all_columns)
    print(f"params = {params}\nfilters = '{filters}'")

    # -- to prevent accidental deletion of everything, at least 1 parameter is required
    # supplied = {'filter': filters} | params if filters else params
    supplied = {{'filter': filters}, params} if filters else params
    query_params = all_columns + ["filter"]
    if not any(k in supplied.keys() for k in query_params):
        res = {"message": "missing a query param(s)", "query_params": query_params, "supplied": supplied}
        return clean(res)

    # -- build "conditions" string and "values" string/array for "updateRow()"
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
#                      User's Table: Additional Functions                     #
###############################################################################
@route("/login", method=["GET", "POST", "PUT", "DELETE"])
@route("/login/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def login(db, url_paths=""):
    # -- parse "params" and "filters" from HTTP request
    required_columns = getColumns(db, table="users", required=True)
    params, filters  = parseUrlPaths(url_paths, request.params, required_columns)
    print(f"params = {params}\nfilters = '{filters}'")

    # -- check for required parameters
    if any(k not in params.keys() for k in required_columns):
        res = {"message": "missing parameters", "required": required_columns, "supplied": params}
        return clean(res)

    # -- check if user exists
    row = fetchRow(db, table="users", where="username=?", values=params["username"])
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

@route("/logout", method=["GET", "POST", "PUT", "DELETE"])
def logout(db):
    # response.delete_cookie("user_id")

    # -- send response message
    res = {"message": "user logged out"}
    return clean(res)

###############################################################################
#                          Database Admin Functions                           #
###############################################################################
@route("/dropTable")
@route("/dropTable/<table>")
def dropTable(db, table=""):
    if table == 'usage':
        return usage_delete_table
    if ((not table) or (table not in [t["name"] for t in getTables(db)])):
        return clean({"message": "active tables in the database", "tables": getTables(db)})

    # -- DROP TABLE <table>
    res = deleteTable(db, table=table)
    res.update({"table": table})
    return clean(res)

@route("/createTable")
@route("/createTable/<table>")
@route("/createTable/<table>/<url_paths:path>", method=["GET", "POST", "PUT", "DELETE"])
def createTable(db, table="", url_paths=""):
    if table == 'usage':
        return usage_create_table
    if ((not table) or (not url_paths)):
        return clean({"message": "active tables in the database", "tables": getTables(db)})

    # -- parse "params" and "url_paths" from HTTP request
    params, columns = mapUrlPaths(url_paths, request.params, table)

    # -- CREATE TABLE <table>
    res = addTable(db, table=table, columns=columns)
    res.update({"table": table})
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


###############################################################################
#                                TESTING / DEBUG                              #
###############################################################################
@route("/test", method=["GET", "POST", "PUT", "DELETE"])
def test(db):
    print(f"request.url = {request.url}")
    print(f"request.urlparts.query = {request.urlparts.query}")
    print(f"request.query_string = {request.query_string}")
    print(f"request.params = {dict(request.params)}")
    return redirect(f'/get/users?{urlencode(request.params)}')


# -- Run Web Server
port = int(os.environ.get("PORT", 8080))
# run(host="0.0.0.0", port=port, reloader=True)
run(app, host="0.0.0.0", port=port, reloader=True)




###############################################################################
#                             DEPRECATED FUNCTIONS                            #
###############################################################################
"""
###############################################################################
#                         User's Table: Core Functions                        #
###############################################################################
@route("/addUser", method=["GET", "POST", "PUT", "DELETE"])
@route("/createUser", method=["GET", "POST", "PUT", "DELETE"])
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

@route("/getUser", method=["GET", "POST", "PUT", "DELETE"])
@route("/getUsers", method=["GET", "POST", "PUT", "DELETE"])
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


@route("/editUser", method=["GET", "POST", "PUT", "DELETE"])
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

@route('/deleteUser', method=["GET", "POST", "PUT", "DELETE"])
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
@route("/addSensorData", method=["GET", "POST", "PUT", "DELETE"])
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

@route("/getSensorData", method=["GET", "POST", "PUT", "DELETE"])
@route("/getAllSensorData", method=["GET", "POST", "PUT", "DELETE"])
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

@route("/editSensorData", method=["GET", "POST", "PUT", "DELETE"])
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

@route("/deleteSensorData", method=["GET", "POST", "PUT", "DELETE"])
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
"""
