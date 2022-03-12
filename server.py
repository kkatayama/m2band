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
    response = {
        "message": "available commands",
        "GET": [{
            "/": {
                "Note": "debug function",
                "Returns": "this list of available commands"
            }}, {
            "/getUsers": {
                "Note": "debug function",
                "Returns": "list of users in the 'users' table"
            }}, {
            "/getAllSensorData": {
                "Note": "debug function",
                "Returns": "Sensor data for all users"
            }}
        ],
        "POST": [{
            "/login": {
                "Params": ["username", "password"],
                "Returns": [{
                    "message": "user does not exist",
                    "username": "username"
                }, {
                    "message": "incorrect password",
                    "password": "password"
                }, {
                    "message": "user login success",
                    "user_id": "user_id",
                    "username": "username"
                }]
            },
            "/createUser": {
                "Params": ["username", "password"],
                "Returns": [{
                    "message": "user exists",
                    "username": "username"
                }, {
                    "message": "user created",
                    "user_id": "user_id",
                    "username": "username"
                }]
            },
            "/getUser": {
                "Params": ["user_id"],
                "Returns": [{
                    "message": "user account details",
                    "data": "json object of user info for 'user_id'"
                }]
            },
            "/addSensorData": {
                "Params": ["user_id", "heart_rate", "blood_o2", "temperature"],
                "Returns": [{
                    "message": "sensor data added for 'user_id'",
                    "user_id": "user_id",
                    "entry_id": "entry_id"
                }]
            },
            "/getSensorData": {
                "Params": ["user_id"],
                "Returns": [{
                    "message": "sensor data for 'user_id'",
                    "data": "list of sensor data for 'user_id'"
                }]
            }
        }]
    }
    print(response)
    return response

###############################################################################
#                            Users Table Functions                            #
###############################################################################
@app.route("/login", method="POST")
def login(db):
    username = request.forms["username"]
    password = request.forms["password"]

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

@app.route("/createUser", method="POST")
def createUser(db):
    username  = request.POST["username"]
    plaintext = request.POST["password"]
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
        "values": [username, password, create_time],
    }
    user_id = insertRow(db, **params)
    response = {
        "message": "user created",
        "user_id": user_id,
        "username": username
    }
    print(response)
    return response

@app.route("/getUsers", method="GET")
def getUsers(db):
    inspect(request.GET)
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


@app.route('/getUser', method="POST")
def getUser(db):
    user_id = request.POST.get('user_id')
    # row = fetchRow(db, table="users", )
    params = {
        "table": "users",
        "where": "user_id=?",
        "values": user_id
    }
    row = fetchRow(db, **params)

    response = {
        "message": "user account details",
        "data": clean(row)
    }
    print(response)
    return response


###############################################################################
#                           Oximeter Table Functions                          #
###############################################################################
@app.route("/addSensorData", method="POST")
def addSensorData(db):
    user_id     = request.POST["user_id"]
    heart_rate  = request.POST["heart_rate"]
    blood_o2    = request.POST["blood_o2"]
    temperature = request.POST["temperature"]
    entry_time  = datetime.now()

    params = {
        "table": "oximeter",
        "columns": ["user_id", "heart_rate", "blood_o2", "temperature", "entry_time"],
        "values": [user_id, heart_rate, blood_o2, temperature, entry_time]
    }
    entry_id = insertRow(db, **params)

    response = {
        "message": "sensor data added for 'user_id'",
        "user_id": user_id,
        "entry_id": entry_id
    }
    print(response)
    return response

@app.route("/getSensorData", method=["POST"])
def getSensorData(db):
    user_id = request.POST["user_id"]
    params = {
        "table": "oximeter",
        "where": "user_id=?",
        "values": user_id
    }
    row = fetchRows(db, **params)

    response = {
        "message": "sensor data for 'user_id'",
        "data": clean(user_data)
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
    all_data = fetchRows(db, **params)

    response = {
        "message": "sensor data for all users",
        "data": clean(all_data)
    }
    print(response)
    return response

# -- Run Web Server
port = int(os.environ.get("PORT", 8080))
run(app, host="0.0.0.0", port=port, reloader=True, debug=True)
