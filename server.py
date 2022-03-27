from bottle import Bottle, request, run, template
from bottle_sqlite import SQLitePlugin, sqlite3
from db_functions import *
from datetime import datetime
# from rich.traceback import install
# from rich import print, inspect, print_json, pretty
import json
import os

# pretty.install()

app = Bottle()
plugin = SQLitePlugin(dbfile="m2band.db", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
app.install(plugin)

@app.route("/", method=["GET", "POST", "PUT", "DELETE"])
def index():
    with open('all_commands.js') as f:
        response = json.load(f)
    print(response)
    return response

###############################################################################
#                            Users Table Functions                            #
###############################################################################
@app.route("/login", method=["GET", "POST", "PUT", "DELETE"])
def login(db):
    table = "users"
    required_params = ["username", "password"]

    # -- parse "params" from HTTP request
    params = {k:v for (k,v) in request.params.items() if k in required_params}
    try:
        # -- local variables (only contains value if passed in request)
        username = params["username"]
        password = params["password"]
    except KeyError:
        response = {
            "message": "missing paramater",
            "required_params": required_params,
            "your_params": dict(request.params),
        }
        print(response)
        return response

    # Check if user exists ####################################################
    # -- build "conditions" string and "values" string/array for "fetchRow()"
    # -- conditions = "username=?"
    # -- values = usernam
    conditions = " AND ".join([f"{option}=?" for option in params.keys()])
    values = list(params.values())

    # -- query database
    # -- SELECT * FROM users WHERE username=?;
    # -- ? = params["username"]
    params = {
        "table": table,
        "where": conditions,
        "values": values
    }
    row = fetchRow(db, **params)

    # -- process the database response
    # -- row contains a value if the "username" exists in the [users] table
    if not row:
        response = {
            "message": "user does not exist",
            "username": username
        }
        print(response)
        return response

    # -- check user supplied password (previous row statement has user data for username=[username])
    if not checkPassword(password, row["password"]):
        # -- checkPassword() returned False
        response = {
            "message": "incorrect password",
            "password": password
        }
        print(response)
        return response

    # -- made it here: means username exists and checkPassword() returned True
    # -- process the database response
    response = {
        "message": "user login success",
        "user_id": row["user_id"],
        "username": row["username"]
    }
    print(response)
    return response

@app.route("/addUser", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/createUser", method=["GET", "POST", "PUT", "DELETE"])
def addUser(db):
    table = "users"
    required_params  = ["username", "password"]

    # -- parse "params" from HTTP request
    params = {k:v for (k,v) in request.params.items() if k in required_params}
    try:
        # -- local variables (only contains value if passed in request)
        username  = params["username"]
        plaintext = params["password"]
    except KeyError:
        response = {
            "message": "missing paramater",
            "required_params": required_params,
            "your_params": dict(request.params),
        }
        print(response)
        return response
    # -- local variables (process "plaintext" and "create_time")
    password    = securePassword(plaintext)
    create_time = datetime.now()

    # Check if user exists ####################################################
    # -- build "conditions" string and "values" string/array for "fetchRow()"
    conditions = "username=?"
    values = username

    # -- query database
    # -- SELECT * FROM users WHERE username=?;
    # -- ? = params["username"]
    params = {
        "table": table,
        "where": conditions,
        "values": values
    }
    row = fetchRow(db, **params)

    # -- process the database response
    # -- row would only contain a value if the "username" exists in the [users] table
    if row:
        response = {
            "message": "user exists",
            "username": row["username"]
        }
        print(response)
        return response

    # If user doesn't exist, create user ######################################
    # -- define "columns" to edit and "values" to insert
    columns  = ["username", "password", "create_time"]
    col_vals = [username, password, create_time]

    # -- query database
    # -- INSERT INTO users (username,password,create_time) VALUES (?, ?, ?);
    params = {
        "table": table,
        "columns": columns,
        "col_values": col_vals,
    }
    user_id = insertRow(db, **params)

    # -- process the database response
    if isinstance(user_id, dict):
        if user_id.get('ProgrammingError'):
            print(rows)
            return rows
    response = {
        "message": "user created",
        "user_id": user_id,
        "username": username
    }
    print(response)
    return response

@app.route("/getUser", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/getUsers", method=["GET", "POST", "PUT", "DELETE"])
def getUser(db):
    table = "users"
    params_options = ["user_id", "username", "password", "create_time"]
    filter_options = ["filter"]

    # -- parse parameters and filters from HTTP request
    params  = {k:v for (k,v) in request.params.items() if k in params_options}
    filters = {k:v for (k,v) in request.params.items() if k in filter_options}

    # -- build "conditions" string and "values" array for "fetchRows()"
    conditions = " AND ".join([f"{option}=?" for option in params.keys()])
    values     = list(params.values())
    if filters.get("filter"):
        filter_conditions, filter_values = parseFilters(filters["filter"], conditions)
        conditions = conditions + filter_conditions
        values     = values + filter_values

    # -- query database
    # -- SELECT * FROM users WHERE (user_id=?);
    params = {
        "table": table,
        "where": conditions,
        "values": values
    }
    rows = fetchRows(db, **params)

    # -- process the database response
    if isinstance(rows, dict):
        if rows.get('ProgrammingError'):
            print(rows)
            return rows
        message = f"found 1 user"
    elif isinstance(rows, list):
        message = f"found {len(rows)} users"

    if rows:
        response = {
            "message": message,
            "data": clean(rows)
        }
        print(response)
        return response

    # -- found 0 users
    response = {
        "message": "found 0 users",
        "your_params": dict(request.params)
    }
    print(response)
    return response

@app.route("/editUser", method=["GET", "POST", "PUT", "DELETE"])
def editUser(db):
    table = "users"
    required_params  = ["user_id"]
    editable_columns = ["username", "password"]
    params_options   = ["user_id", "username", "password"]

    # -- parse "params" from HTTP request
    params = {k:v for (k,v) in request.params.items() if k in params_options}
    try:
        user_id = params["user_id"]
        if not any(params.get(k) for k in editable_columns):
            raise KeyError
    except KeyError:
        response = {
            "message": "missing paramater",
            "required_params": required_params,
            "editable param(s)": editable_columns,
            "your_params": dict(request.params),
        }
        print(response)
        return response

    # -- local variables
    username  = params.get("username")
    plaintext = params.get("password")
    if plaintext:
        password = securePassword(plaintext)
        params.update({"password": password})

    # -- define "columns" to edit and "values" to insert (parsed from params in HTTP request)
    columns    = [column for column in editable_columns if params.get(column)]
    col_values = [params[column] for column in columns]

    # -- build "conditions" string and "values" string/array for "updateRow()"
    conditions = " AND ".join([f"{param}=?" for param in required_params])
    values     = [params[param] for param in required_params]

    # -- query database
    # -- UPDATE users SET username=? WHERE (user_id=?);
    params = {
        "table": table,
        "columns": columns,
        "col_values": col_values,
        "where": conditions,
        "values": values
    }
    num_edits = updateRow(db, **params)

    # -- process the database response
    if isinstance(num_edits, dict):
        if num_edits.get('ProgrammingError'):
            print(rows)
            return rows

    if num_edits:
        response = {
            "message": f"user edited",
            "user_id": user_id
        }
        print(response)
        return response

    # -- user not found
    response = {
        "message": "user not found",
        "your_params": dict(request.params)
    }
    print(response)
    return response

@app.route('/deleteUser', method=["GET", "POST", "PUT", "DELETE"])
def deleteUser(db):
    table = "users"
    required_params = ["user_id"]

    # -- parse "params" from HTTP request
    params = {k:v for (k,v) in request.params.items() if k in required_params}
    try:
        user_id = params["user_id"]
    except KeyError:
        response = {
            "message": "missing paramater",
            "required_params": required_params,
            "your_params": dict(request.params),
        }
        print(response)
        return response

    # -- build "conditions" string and "values" string/array for "deleteRow()"
    conditions = " AND ".join([f"{param}=?" for param in required_params])
    values     = [params[param] for param in required_params]

    # -- query database
    # -- DELETE FROM users WHERE (user_id=?);
    params = {
        "table": table,
        "where": conditions,
        "values": values
    }
    num_deletes = deleteRow(db, **params)

    # -- process the database response
    if isinstance(num_deletes, dict):
        if num_deletes.get('ProgrammingError'):
            print(rows)
            return rows

    if num_deletes:
        response = {
            "message": "user deleted",
            "user_id": user_id
        }
        print(response)
        return response

    # -- either: bad request OR database error
    response = {
        "message": "user delete error"
    }
    print(response)
    return response

###############################################################################
#                           Oximeter Table Functions                          #
###############################################################################
@app.route("/addSensorData", method=["GET", "POST", "PUT", "DELETE"])
def addSensorData(db):
    table = "oximeter"
    required_params = ["user_id", "heart_rate", "blood_o2", "temperature"]

    # -- parse "params" from HTTP request
    params = {k:v for (k,v) in request.params.items() if k in required_params}
    try:
        user_id     = params["user_id"]
        heart_rate  = params["heart_rate"]
        blood_o2    = params["blood_o2"]
        temperature = params["temperature"]
    except KeyError:
        response = {
            "message": "missing paramater",
            "required_params": required_params,
            "your_params": dict(request.params),
        }
        print(response)
        return response
    entry_time = datetime.now()

    # -- define "columns" to edit and "values" to insert
    columns  = ["user_id", "heart_rate", "blood_o2", "temperature", "entry_time"]
    col_vals = [user_id, heart_rate, blood_o2, temperature, entry_time]

    # -- query database
    params = {
        "table": table,
        "columns": columns,
        "col_values": col_vals
    }
    entry_id = insertRow(db, **params)

    # -- process the database response
    if isinstance(entry_id, dict):
        if entry_id.get('ProgrammingError'):
            print(rows)
            return rows
    response = {
        "message": "sensor data added",
        "user_id": user_id,
        "entry_id": entry_id
    }
    print(response)
    return response

@app.route("/getSensorData", method=["GET", "POST", "PUT", "DELETE"])
@app.route("/getAllSensorData", method=["GET", "POST", "PUT", "DELETE"])
def getSensorData(db):
    table = "oximeter"
    params_options = ["entry_id", "user_id", "heart_rate", "blood_o2", "temperature", "entry_time"]
    filter_options = ["filter"]

    # -- parse parameters and filters from HTTP request
    params  = {k:v for (k,v) in request.params.items() if k in params_options}
    filters = {k:v for (k,v) in request.params.items() if k in filter_options}

    # -- build "conditions" string and "values" array for "fetchRows()"
    conditions = " AND ".join([f"{option}=?" for option in params.keys()])
    values     = list(params.values())
    if filters.get("filter"):
        filter_conditions, filter_values = parseFilters(filters["filter"], conditions)
        conditions = conditions + filter_conditions
        values     = values + filter_values

    # -- query database
    # -- SELECT * FROM users WHERE (user_id=?);
    params = {
        "table": table,
        "where": conditions,
        "values": values
    }
    rows = fetchRows(db, **params)

    # -- process the database response
    if isinstance(rows, dict):
        if rows.get('ProgrammingError'):
            print(rows)
            return rows
        message = f"found 1 entry"
    elif isinstance(rows, list):
        message = f"found {len(rows)} entries"

    if rows:
        response = {
            "message": message,
            "data": clean(rows)
        }
        print(response)
        return response

    # -- found 0 entries
    response = {
        "message": "found 0 entries",
        "your_params": dict(request.params)
    }
    print(response)
    return response

@app.route("/editSensorData", method=["GET", "POST", "PUT", "DELETE"])
def editSensorData(db):
    table = "oximeter"
    required_params  = ["user_id"]
    editable_columns = ["heart_rate", "blood_o2", "temperature"]
    params_options = ["user_id", "heart_rate", "blood_o2", "temperature"]
    filter_options = ["filter"]

    # -- parse "params" from HTTP request
    params  = {k:v for (k,v) in request.params.items() if k in params_options}
    filters = {k:v for (k,v) in request.params.items() if k in filter_options}
    try:
        user_id = params["user_id"]
        if not any(params.get(k) for k in editable_columns):
            raise KeyError
    except KeyError:
        response = {
            "message": "missing paramaters",
            "required_params": required_params,
            "editable_param(s)": editable_columns,
            "optional_param(s)": ["entry_id", "filter"],
            "your_params": dict(request.params),
        }
        print(response)
        return response

    # -- local variables
    heart_rate  = params.get("heart_rate")
    blood_o2    = params.get("blood_o2")
    temperature = params.get("temperature")
    entry_id    = params.get("entry_id")

    # -- define "columns" to edit and "values" to insert (parsed from params in HTTP request)
    columns    = [column for column in editable_columns if params.get(column)]
    col_values = [params[column] for column in columns]

    # -- build "conditions" string and "values" string/array for "updateRow()"
    conditions = " AND ".join([f"{option}=?" for option in params_options])
    values     = [params[param] for param in params_options]
    if filters.get("filter"):
        filter_conditions, filter_values = parseFilters(filters["filter"], conditions)
        conditions = conditions + filter_conditions
        values     = values + filter_values

    # -- query database
    params = {
        "table": table,
        "columns": columns,
        "col_values": col_values,
        "where": conditions,
        "values": values
    }
    num_edits = updateRow(db, **params)

    # -- process the database response
    if isinstance(num_edits, dict):
        if num_edits.get('ProgrammingError'):
            print(rows)
            return rows

    if num_edits:
        response = {
            "message": f"{num_edits} entries edited for 'user_id = {user_id}'"
        }
        print(response)
        return response

    # -- no entries edited
    response = {
        "message": "found no entries matching your parameters",
        "your_params": dict(request.params)
    }

@app.route("/deleteSensorData", method=["GET", "POST", "PUT", "DELETE"])
def deleteSensorData(db):
    table = "oximeter"
    required_params = ["user_id"]
    params_options  = ["entry_id", "user_id", "heart_rate", "blood_o2", "temperature", "entry_time"]
    filter_options  = ["filter"]

    # -- parse parameters and filters from HTTP request
    params  = {k:v for (k,v) in request.params.items() if k in params_options}
    filters = {k:v for (k,v) in request.params.items() if k in filter_options}
    try:
        user_id = params["user_id"]
    except KeyError:
        response = {
            "message": "missing paramater(s)",
            "required_params": required_params,
            "optional params": ["entry_id", "filter"],
            "your_params": dict(request.params),
        }
        print(response)
        return response
    entry_id = params.get("entry_id")

    # -- build "conditions" string and "values" string/array for "deleteRow()"
    conditions = " AND ".join([f"{option}=?" for option in params_options])
    values     = [params[param] for param in params_options]
    if filters.get("filter"):
        filter_conditions, filter_values = parseFilters(filters["filter"], conditions)
        conditions = conditions + filter_conditions
        values     = values + filter_values

    # -- query database
    params = {
        "table": table,
        "where": conditions,
        "values": values
    }
    num_deletes = deleteRow(db, **params)

    # -- process the database response
    if isinstance(num_deletes, dict):
        if num_deletes.get('ProgrammingError'):
            print(rows)
            return rows

    if num_deletes:
        response = {
            "message": f"deleted {num_deletes} sensor data entries"
        }
        print(response)
        return response

        # -- no entries edited
    response = {
        "message": "found no entries to delete matching your parameters",
        "your_params": dict(request.params)
    }


# -- Run Web Server
port = int(os.environ.get("PORT", 8080))
run(app, host="0.0.0.0", port=port, reloader=True)
