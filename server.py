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

@app.route("/", method=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
def index():
    with open('all_commands.js') as f:
        response = json.load(f)
    print(response)
    return response

###############################################################################
#                            Users Table Functions                            #
###############################################################################
@app.route("/login", method=["GET", "POST"])
def login(db):
    try:
        username = eval(f"request.{request.method}.get('username')")
        password = eval(f"request.{request.method}.get('password')")
        # username = request.POST["username"]
        # password = request.POST["password"]
    except KeyError:
        response = {
            "message": "missing paramater",
            "required params": ["username", "password"]
        }
        print(response)
        return response

    # -- check if user exists
    params = {
        "table": "users",
        "where": "username=?",
        "values": username
    }
    row = fetchRow(db, **params)
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
    response = {
        "message": "user login success",
        "user_id": row["user_id"],
        "username": row["username"]
    }
    print(response)
    return response

@app.route("/createUser", method=["GET", "POST"])
def createUser(db):
    try:
        username  = eval(f"request.{request.method}.get('username')")
        plaintext = eval(f"request.{request.method}.get('password')")
        # username  = request.POST["username"]
        # plaintext = request.POST["password"]
    except KeyError:
        response = {
            "message": "missing paramater",
            "required params": ["username", "password"]
        }
        print(response)
        return response
    password  = securePassword(plaintext)
    create_time = datetime.now()

    # -- check if user exists
    params = {
        "table": "users",
        "where": "username=?",
        "values": username
    }
    row = fetchRow(db, **params)
    if row:
        response = {
            "message": "user exists",
            "username": row["username"]
        }
        print(response)
        return response

    # -- if user doesn't exist, create user
    params = {
        "table": "users",
        "columns": ["username", "password", "create_time"],
        "col_values": [username, password, create_time],
    }
    user_id = insertRow(db, **params)

    response = {
        "message": "user created",
        "user_id": user_id,
        "username": username
    }
    print(response)
    return response

@app.route("/editUser", method=["GET", "PUT", "POST"])
def editUser(db):
    user_id   = eval(f"request.{request.method}.get('user_id')")
    username  = eval(f"request.{request.method}.get('username')")
    plaintext = eval(f"request.{request.method}.get('password')")

    # -- are we changing the (username) and (password)?
    if (username and plaintext):
        password = securePassword(plaintext)

        params = {
            "table": "users",
            "columns": ["username", "password"],
            "col_values": [username, password],
            "where": "user_id=?",
            "values": user_id
        }
        num_edits = updateRow(db, **params)

        if num_edits:
            response = {
                "message": "user edited",
                "user_id": user_id
            }
            print(response)
            return response

    # -- or just the (password)?
    elif (plaintext):
        password = securePassword(plaintext)

        params = {
            "table": "users",
            "columns": ["password"],
            "col_values": [password],
            "where": "user_id=?",
            "values": user_id

        }
        num_edits = updateRow(db, **params)

        if num_edits:
            response = {
                "message": "user edited",
                "user_id": user_id
            }
            print(response)
            return response

    # -- or just the (username)
    elif (username):
        params = {
            "table": "users",
            "columns": ["username"],
            "col_values": [username],
            "where": "user_id=?",
            "values": user_id
        }
        num_edits = updateRow(db, **params)

        if num_edits:
            response = {
                "message": "user edited",
                "user_id": user_id
            }
            print(response)
            return response

    # -- either: bad request OR database error
    response = {
        "message": "user edit error"
    }
    print(response)
    return response

@app.route('/deleteUser', method=["GET", "DELETE", "POST"])
def deleteUser(db):
    try:
        user_id = eval(f"request.{request.method}.get('user_id')")
    except KeyError:
        response = {
            "message": "missing paramater",
            "required params": ["user_id"]
        }
        print(response)
        return response

    params = {
        "table": "users",
        "where": "user_id=?",
        "values": user_id
    }
    num_deletes = deleteRow(db, **params)

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

@app.route('/getUser', method=["GET", "POST"])
def getUser(db):
    try:
        user_id  = eval(f"request.{request.method}.get('user_id')")
        # user_id = request.POST.get('user_id')
    except KeyError:
        response = {
            "message": "missing paramater",
            "required params": ["user_id"]
        }
        print(response)
        return response

    params = {
        "table": "users",
        "where": "user_id=?",
        "values": user_id
    }
    row = fetchRow(db, **params)

    if row:
        response = {
            "message": "user account details",
            "data": clean(row)
        }
        print(response)
        return response

    # -- either: bad request OR database error
    response = {
        "message": "user get error"
    }
    print(response)
    return response

@app.route("/getUsers", method="GET")
def getUsers(db):
    """
    This function is here for debugging purposes
    """
    params = {"table": "users"}
    rows = fetchRows(db, **params)

    response = {
        "message": f"found {len(rows)} users",
        "users": clean(rows)
    }
    print(response)
    return response

###############################################################################
#                           Oximeter Table Functions                          #
###############################################################################
@app.route("/addSensorData", method=["GET", "POST"])
def addSensorData(db):
    try:
        user_id       = eval(f"request.{request.method}.get('user_id')")
        heart_rate    = eval(f"request.{request.method}.get('heart_rate')")
        blood_o2      = eval(f"request.{request.method}.get('blood_o2')")
        temperature   = eval(f"request.{request.method}.get('temperature')")
        # user_id     = request.POST["user_id"]
        # heart_rate  = request.POST["heart_rate"]
        # blood_o2    = request.POST["blood_o2"]
        # temperature = request.POST["temperature"]
    except KeyError:
        response = {
            "message": "missing paramater",
            "required params": ["user_id", "heart_rate", "blood_o2", "temperature"]
        }
        print(response)
        return response
    entry_time  = datetime.now()

    params = {
        "table": "oximeter",
        "columns": ["user_id", "heart_rate", "blood_o2", "temperature", "entry_time"],
        "col_values": [user_id, heart_rate, blood_o2, temperature, entry_time]
    }
    entry_id = insertRow(db, **params)

    response = {
        "message": "sensor data added for 'user_id'",
        "user_id": user_id,
        "entry_id": entry_id
    }
    print(response)
    return response

@app.route("/getSensorData", method=["GET", "POST"])
def getSensorData(db):
    try:
        user_id = eval(f"request.{request.method}.get('user_id')")
        # user_id = request.POST["user_id"]
    except KeyError:
        response = {
            "message": "missing paramater",
            "required params": ["user_id"]
        }
        print(response)
        return response

    params = {
        "table": "oximeter",
        "where": "user_id=?",
        "values": user_id
    }
    row = fetchRow(db, **params)

    response = {
        "message": "sensor data for 'user_id'",
        "data": clean(row)
    }
    print(response)
    return response

@app.route("/getAllSensorData", method=["GET"])
def getAllSensorData(db):
    """
    This function is here for debugging purposes
    """
    params = {
        "table": "oximeter"
    }
    rows = fetchRows(db, **params)

    response = {
        "message": "sensor data for all users",
        "data": clean(rows)
    }
    print(response)
    return response

# -- Run Web Server
port = int(os.environ.get("PORT", 8080))
run(app, host="0.0.0.0", port=port, reloader=True)
