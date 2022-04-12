#!/usr/bin/env python3

usage_add = {
    "message": "usage info: '/add'",
    "description": "add a single entry into a table: <table_name>",
    "endpoints": {
        "/add": {
            "returns": "returns all tables[] in the database",
        },
        "/add/usage": {
            "returns": "message: 'usage-info",
        },
        "/add/<table_name>": {
            "returns": "message: 'missing parameters'",
        },
        "/add/<table_name>/<param_name>/<param_value>": {
            "url_paths": "add entry: 'param_name=param_value'",
            "example": "/add/users/username/user_01/password/user_01",
            "response": {
                "message": "data added to {users}",
                "user_id": 8
            },
        },
        "/add/<table_name>?param_name=param_value": {
            "params": "add entry: 'param_name=param_value'",
            "example": "/add/users?username=user_01&password=user_01",
            "response": {
                "message": "data added to {users}",
                "user_id": 8
            },
        },
        "Required": "'user_id' and all params not '*_id' and '*_time'",
        "Exception": "no 'user_id' when adding to the users table",
        "Response": {
            "'user_id'": "when entry added to 'users' table",
            "'<ref>_id'": "when entry added to any other table",
        },
    },
}

usage_get = {
    "message": "usage info: '/get'",
    "description": "fetch entry/entries from a table: <table_name>",
    "endpoints": {
        "/get": {
            "returns": "return all tables[] in the database",
        },
        "/get/usage": {
            "returns": "{'message': 'usage-info'}",
        },
        "/get/<table_name>": {
            "returns": "returns all entries for the table: <table_name>",
        },
        "/get/<table_name>/<param_name>/<param_value>": {
            "url_paths": "match entries: 'param_name=param_value'",
            "example": "/get/users/username/bob",
            "response": {
                "message": "1 user entry found",
                "data": {
                    "user_id": 8, "username": "bob", "password": "8..4", "create_time": "2022-04-05 03:25:57.163"
                },
            },
        },
        "/get/<table_name>?param_name=param_value": {
            "params": "match entries: 'param_name=param_value'",
            "example": "/get/users?user_id=8",
            "response": {
                "message": "1 user entry found",
                "data": {
                    "user_id": 8, "username": "bob", "password": "8..4", "create_time": "2022-04-05 03:25:57.163"
                },
            },
        },
        "/get/<table_name>/filter/query": {
            "url_paths": "match entries: 'filter=[query]'",
            "example": "/get/oximeter/filter/(temperature > '100.4') GROUP BY user_id",
            "response": {
                "message": "1 oximeter entry found",
                "data": {
                    "entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.71, "entry_time": "2022-04-05 12:16:54.651"
                },
            },
        },
        "/get/<table_name>?filter=query": {
            "params": "match entries: 'filter=[query]'",
            "example": "/get/users?filter=(create_time > \"2022-04-03\")",
            "response": {
                "message": "found 3 user entries",
                "data": [
                    {"user_id": 6, "username": "M2band", "password": "3..4", "create_time": "2022-04-03 15:29:41.223"},
                    {"user_id": 7, "username": "alice@udel.edu", "password": "d..a", "create_time": "2022-04-05 03:25:57.163"},
                    {"user_id": 8, "username": "robert@udel.edu", "password": "8..4", "create_time": "2022-04-05 03:41:12.857"},
                ],

            },
        },
        "Options": {
            "Parameters": {
                "None": "submit no parameters (none required)",
                "/key/value": "match is limited to 'column_name == column_value'",
                "?key=value": "match is limited to 'column_name == column_value'",
                "/filter/query": "supports expressions, operators, and functions",
                "?filter=query": "supports expressions, operators, and functions",
            }
        },
        "Response": {
            "data": {
                "{object}": "a single object matching the parameters",
                "[{object}]": "a single object matching the parameters"
            }
        },
    },
}



usage_edit = {
    "message": "usage info: '/edit'",
    "description": "edit entry/entries from a table: <table_name>",
    "endpoints": {
        "/edit": {
            "returns": "return all tables[] in the database",
        },
        "/edit/usage": {
            "returns": "message: 'usage-info'",
        },
        "/edit/<table_name>": {
            "returns": "message: 'missing a parameter'",
        },
        "/edit/<table_name>/<param_name>/<param_value>": {
            "url_paths": "edit entries: 'param_name=param_value'",
            "example": "/edit/users/username/robert?user_id=8",
            "response": {
                "message": "edited 1 user entry",
                "submitted": [{"username": "robert", "user_id": "8"}]
            },
        },
        "/edit/<table_name>?param_name=param_value": {
            "params": "edit entries: 'param_name=param_value'",
            "example": "/edit/users/username/robert?user_id=8",
            "response": {
                "message": "edited 1 user entry",
                "submitted": [{"username": "robert", "user_id": "8"}]
            },
        },
        "/edit/<table_name>/filter/query": {
            "url_paths": "edit entries: 'filter=[query]'",
            "example": "/edit/oximeter/temperature/(temperature-32.0)*(5.0/9.0)?filter=(user_id='7')",
            "response": {
                "message": "edited 6 oximeter entries",
                "submitted": [{
                    "filter": "(user_id='7')",
                    "temperature": "((5.0/9.0)*(temperature-32.0))"
                }]
            },
        },
        "/edit/<table_name>?filter=query": {
            "params": "edit entries: 'filter=[query]'",
            "example": "/edit/oximeter/temperature/(temperature-32.0)*(5.0/9.0)?filter=(user_id='7')",
            "response": {
                "message": "edited 6 oximeter entries",
                "submitted": [{
                    "filter": "(user_id='7')",
                    "temperature": "((5.0/9.0)*(temperature-32.0))"
                }]
            },
        },
        "Required": {
            "Parameters": {
                "at least 1 edit parameter": "any parameter not '*_id' or '*_time'",
                "at least 1 reference parameter": "any '*_id' or '*_time' parameter or 'filter'"
                }
        },
        "Response": {
            "message": "number of edits made",
            "submitted[]": "the parameters that were submitted",
        },
    },
}

usage_delete = {
    "message": "usage info: '/delete'",
    "description": "delete entry/entries from a table: <table_name>",
    "endpoints": {
        "/delete": {
            "returns": "return all tables[] in the database",
        },
        "/delete/usage": {
            "returns": "{'message': 'usage-info'}",
        },
        "/delete/<table_name>": {
            "returns": "message: 'missing a parameter'",
        },
        "/delete/<table_name>/<param_name>/<param_value>": {
            "url_paths": "delete entries: 'param_name=param_value'",
            "example": "/delete/oximeter?filter=(user_id = '8' AND temperature > '100.4')",
            "response": {
                "message": "6 oximeter entries deleted",
                "submitted": [{"filter": "(user_id = '8' AND temperature > '100.4')"}]
            },
        },
        "/delete/<table_name>?param_name=param_value": {
            "params": "delete entries: 'param_name=param_value'",
            "example": "/delete/oximeter?filter=(user_id = '8' AND temperature > '100.4')",
            "response": {
                "message": "6 oximeter entries deleted",
                "submitted": [{"filter": "(user_id = '8' AND temperature > '100.4')"}]
            },
        },
        "/delete/<table_name>/filter/query": {
            "url_paths": "delete entries: 'filter=[query]'",
            "example": "/delete/oximeter?filter=(user_id = '8' AND temperature > '100.4')",
            "response": {
                "message": "6 oximeter entries deleted",
                "submitted": [{"filter": "(user_id = '8' AND temperature > '100.4')"}]
            },
        },
        "/delete/<table_name>?filter=query": {
            "params": "delete entries: 'filter=[query]'",
            "example": "/delete/oximeter?filter=(user_id = '8' AND temperature > '100.4')",
            "response": {
                "message": "6 oximeter entries deleted",
                "submitted": [{"filter": "(user_id = '8' AND temperature > '100.4')"}]
            },
        },
        "Required": {
            "Parameters": {
                "at least 1 reference parameter": "any '*_id' or '*_time' parameter or 'filter'"
                }
        },
        "Response": {
            "message": "number of deletes made",
            "submitted[]": "the parameters that were submitted",
        },
    },
}



usage_delete_table = {
    "message": "usage info: /deleteTable",
    "description": "delete a table from the database",
    "end_points": {
        "/deleteTable": {
            "returns": "a list of all tables in the database"
        },
        "/deleteTable/<table_name>": {
            "url_paths": [{
                "<table_name>": "the name of the table you want to delete"
            }],
            "returns": [{
                "json response": "confirmation message of table deleted"
            }],
            "notes": [{
                "/deleteTable/users": "you define the table_name by placing it in the '/url_path'"
            }],
        },
    },
}

usage_create_table = {
    "message": "usage info: /createTable",
    "description": "create a table and insert it into the database",
    "end_points": {
        "/createTable": {
            "returns": "a list of all tables in the database"
        },
        "/createTable/<table_name>": {
            "url_paths": [{
                "<table_name>": "the name of the table you want to create"
            }],
            "returns": [{
                "json response": "confirmation message of table created"
            }],
            "notes": [{
                "/createTable/users": "you define the table_name by placing it in the '/url_path'"
            }],
        },
    },
}

usage_login = {
    "message": "usage info: /login",
    "description": "login a user",
    "end_points": {
        "/login": {
            "returns": "message: 'missing parameters'"
        },
        "/login/<param_name>/<param_value>": {
            "url_paths": "login with: 'param_name=param_value'",
            "example": "",
            "response": {

            },
        },
        "/login?param_name=param_value": {
            "params": "login with: 'param_name=param_value'",
            "example": "",
            "response": {

            },
        },
        "Required": {
            "Parameters": {
                "at least 1 reference parameter": "any '*_id' or '*_time' parameter or 'filter'"
                }
        },
        "Response": {
            "message": "number of deletes made",
            "submitted[]": "the parameters that were submitted",
        },
    },
}

usage_logout = {
    "message": "usage info: /logout",
    "description": "logout a user",
    "end_points": {
        "/logout": {
            "returns": "message: 'user logged out'"
        },
    },

}
