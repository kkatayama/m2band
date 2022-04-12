#!/usr/bin/env python3

usage_add = {
    "message": "usage info: '/add'",
    "description": "add a single entry into a table: <table_name>",
    "endpoints": {
        "/add": {
            "returns": "returns all tables[] in the database",
        },
        "/add/usage": {
            "returns": "{'message': 'usage-info'}",
        }
        "/add/<table_name>": {
            "returns": "message containing 'required parameters'",
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
        }
        "/get/<table_name>": {
            "returns": "returns all entries for the table: <table_name>",
        },
        "/get/<table_name>/<param_name>/<param_value>": {
            "url_paths": "match entry: 'param_name=param_value'",
            "example": "/get/users/username/bob",
            "response": {
                "message": "1 user entry found",
                "data": {
                    "user_id": 8, "username": "bob", "password": "8..4", "create_time": "2022-04-05 03:25:57.163"
                },
            },
},
        },
        "/get/<table_name>?param_name=param_value": {
            "params": "match entry: 'param_name=param_value'",
            "example": "/get/users?user_id=8",
            "response": {
                "message": "1 user entry found",
                "data": {
                    "user_id": 8, "username": "bob", "password": "8..4", "create_time": "2022-04-05 03:25:57.163"
                },
            },
        },
        "/get/<table_name>/filter/query": {
            "url_paths": "match entry: 'filter=[query]'",
            "example": "/get/oximeter/filter/(temperature > "100.4") GROUP BY user_id",
            "response": {
                "message": "1 oximeter entry found",
                "data": {
                    "entry_id": 53, "user_id": 8, "heart_rate": 133, "blood_o2": 95, "temperature": 101.71, "entry_time": "2022-04-05 12:16:54.651"
                },
            },
        },
        "/get/<table_name>?filter=query": {
            "params": "match entry: 'filter=[query]'",
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
        "Required": "",
        "Exception": "",
        "Response": {
            "": "",
            "": "",
        },
    },
}

usage_get = {
    "message": "usage info",
    "description": "fetch a single entry or multiple entries in a table",
    "/get": "returns a list of existing tables",
    "/get/<table>": "returns all rows in a table",
    "method_1": "exclusively using url paths",
    "/get/<table>/<param_name>/<param_value>/../..": "find rows matching [name='value', ...]",
    "/get/<table>/filter/<filter_string>": "query rows with filter (create_time > '2022-03-30')",
    "/get/<table>/<param_name>/<param_value>/../../filter/<filter_string>": "match and query filter",
    "method_2": "exclusively using parameters",
    "/get/<table>?param_name=param_value...": "query rows matching [name='value', ...]",
    "/get/<table>?filter='filter_string'": " rows with filter (create_time > '2022-03-30')",
    "/get/<table?param_name=param_value&..&filter='filter_string'": "match and query filter",
    "method_3": "using both parameters and url paths",
    "/get/<table>/<param_name>/<param_value>?filter='filter_string'": "match params and filter",
    "/get/<table>/filter/<filter_string>?param_name=param_value": "filter and match params",
    "returns (multiple)": "an array of json objects for multiple items: [{'user_id': '1', ...}]",
    "returns (single)": "a single json object for 1 item: {'user_id': '4', ...}",
}


usage_edit = {
    "message": "usage info",
    "description": "edit a single entry or multiple entries in a table",
    "/edit": "returns a list of existing tables",
    "/edit/<table>": "returns all rows in a table",
    "/edit/<table>/<column_name>/<column_value>/../..": "query rows matching [name='value', ...]",
    "/edit/<table>/filter/<filter_string>": "query rows with filter (create_time > '2022-03-30')",
    "/edit/<table>/<column_name>/<column_value>/../filter/<filter_string>": "use query and filter"
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
        }
        "/get/<table_name>": {
            "returns": "",
        },
        "/get/<table_name>/<param_name>/<param_value>": {
            "url_paths": "match entry: 'param_name=param_value'",
            "example": "/get/users/username/user_01",
            "response": {
                "message": "",
                "user_id": 8
            },
        },
        "/get/<table_name>?param_name=param_value": {
            "params": "match entry: 'param_name=param_value'",
            "example": "/get/users?username=user_01",
            "response": {
                "message": "",
                "user_id": 8
            },
        },
        "/get/<table_name>/filter/query": {
            "url_paths": "match entry: 'filter=[query]'",
            "example": "/get/users/filter/",
            "response": {
                "message": "",
                "user_id": 8
            },
        },
        "/get/<table_name>?filter=query": {
            "params": "match entry: 'filter=[query]'",
            "example": "/get/users?filter=",
            "response": {
                "message": "",
                "user_id": 8
            },
        },
        "Required": "",
        "Exception": "",
        "Response": {
            "": "",
            "": "",
        },
    },
}


usage_delete = {
    "message": "usage info",
    "description": "delete a single entry or multiple entries from a table",
    "/delete": "returns a list of existing tables",
    "/delete/<table>": "returns all rows in a table",
    "/delete/<table>/<column_name>/<column_value>/../..": "query rows matching [name='value', ...]",
    "/delete/<table>/filter/<filter_string>": "query rows with filter (create_time > '2022-03-30')",
    "/delete/<table>/<column_name>/<column_value>/../filter/<filter_string>": "use query and filter"
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
        }
        "/get/<table_name>": {
            "returns": "",
        },
        "/get/<table_name>/<param_name>/<param_value>": {
            "url_paths": "match entry: 'param_name=param_value'",
            "example": "/get/users/username/user_01",
            "response": {
                "message": "",
                "user_id": 8
            },
        },
        "/get/<table_name>?param_name=param_value": {
            "params": "match entry: 'param_name=param_value'",
            "example": "/get/users?username=user_01",
            "response": {
                "message": "",
                "user_id": 8
            },
        },
        "/get/<table_name>/filter/query": {
            "url_paths": "match entry: 'filter=[query]'",
            "example": "/get/users/filter/",
            "response": {
                "message": "",
                "user_id": 8
            },
        },
        "/get/<table_name>?filter=query": {
            "params": "match entry: 'filter=[query]'",
            "example": "/get/users?filter=",
            "response": {
                "message": "",
                "user_id": 8
            },
        },
        "Required": "",
        "Exception": "",
        "Response": {
            "": "",
            "": "",
        },
    },
}



usage_drop_table = {
    "message": "usage info",
    "description": "delete a table from the database",
    "end_points": {
        "/dropTable": {
            "returns": "a list of all tables in the database"
        },
        "/dropTable/<table_name>": {
            "url_paths": [{
                "<table_name>": "the name of the table you want to delete"
            }],
            "returns": [{
                "json response": "confirmation message of table deleted"
            }],
            "notes": [{
                "/dropTable/users": "you define the table_name by placing it in the '/url_path'"
            }],
        },
    },
}

usage_create_table = {
    "message": "usage info",
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
