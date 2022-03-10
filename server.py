from bottle import Bottle, request, run
from bottle_sqlite import SQLitePlugin
from db_functions import *
from datetime import datetime
import os


app = Bottle()
plugin = SQLitePlugin(dbfile="m2band.db")
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
            "/addSensorData": {
                "Params": ["user_id", "heart_rate", "blood_o2", "temperature", "entry_time"],
                "Returns": [{
                    "message": "data added",
                    "user_id": "user_id",
                    "entry_id": "entry_id"
                }]
            },
            "/getSensorData": {
                "Params": ["user_id"],
                "Returns": [{
                    "message": "user_data",
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
    row = fetchRow(db, table="users", condition="username=?", query_params=[username])
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
    username  = request.forms["username"]
    plaintext = request.forms["password"]

    password = securePassword(plaintext)
    create_time = datetime.now()

    # -- check if user exists
    row = fetchRow(db, table="users", condition="username=?", query_params=[username])
    if row:
        response = {
            "message": "user exists",
            "username": username
        }
        print(response)
        return response

    # -- if user doesn't exist, create user
    # query = "INSERT INTO users (username,password,create_time) VALUES (?, ?, ?) RETURNING user_id;"
    # row = db.execute(query, [username, hash_pass, create_time])
    columns = ["username", "password", "create_time"]
    params  = [username, password, create_time]
    user_id = insertRow(db, table="users", columns=columns, query_params=params)
    response = {
        "message": "user created",
        "user_id": user_id,
        "username": username
    }
    print(response)
    return response

@app.route("/getUsers", method="GET")
def getUsers(db):
    """
    This function is here for debugging purposes
    """
    users = fetchRows(db, table="users")
    response = {
        "message": "users",
        "users": users
    }
    print(response)
    return response

@app.route("/addSensorData", method="POST")
def addSensorData(db):
    user_id     = request.forms["user_id"]
    heart_rate  = request.forms["heart_rate"]
    blood_o2    = request.forms["blood_o2"]
    temperature = request.forms["temperature"]
    entry_time  = datetime.now()

    columns = ["user_id", "heart_rate", "blood_o2", "temperature", "entry_time"]
    params  = [user_id, heart_rate, blood_o2, temperature, entry_time]
    entry_id = insertRow(db, table="oximeter", columns=columns, query_params=params)
    response = {
        "message": "data added",
        "user_id": user_id,
        "entry_id": entry_id
    }
    print(response)
    return response

@app.route("/getSensorData", method=["POST"])
def getSensorData(db):
    print(request.query.__dict__)
    print(request.forms.__dict__)
    print(request.params.__dict__)
    user_id = request.forms["user_id"]

    user_data = fetchRows(db, table="oximeter", condition="user_id=?", query_params=[user_id])
    response = {
        "message": "user_data",
        "data": user_data
    }
    print(response)
    return response

@app.route("/getAllSensorData", method=["GET"])
def getAllSensorData(db):
    """
    This function is here for debugging purposes
    """
    all_data = fetchRows(db, table="oximeter")
    response = {
        "message": "all sensor data",
        "data": all_data
    }
    print(response)
    return response

# -- Run Web Server
port = int(os.environ.get("PORT", 8080))
run(app, host="0.0.0.0", port=port, reloader=True)
