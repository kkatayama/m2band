#!/usr/bin/env python3

usage_add = {
    "message": "usage info",
    "description": "add a single entry into a table: <table_name>",
    "endpoints": {
        "/add": {
            "returns": "return tables[] in the database"
        },
        "/add/usage": {
            "returns": "{'message': 'usage-info'}"
        }
        "/add/<table_name>": {
            "returns": "message containing 'required parameters'",
        },
        "/add/<table>/<param_name>/<param_value>": {
            "url_paths": "you can assing columns to values using url_paths separated by '/'",
            "example": "/add/users/username/user_01/password/user_01"
        },
        "/add/<table>?param_name=param_value": {
            "params": "you can also assign columns to values using parameters",
            "example": "/add/users?username=user_01&password=user_01"
        },
        "Required": "'user_id' and all parameters excluding '{ref}_id' and '{ref}_time'",
        "Exception": "'user_id' is NOT PERMITTED when adding to the  users table"
        "note": "all tables excluding 'users' table require 'user_id' parameter as well",
        "returns": "'user_id' for 'users' table, '<name>_id' for all others (ex: 'entry_id')",
    }
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

usage_delete = {
    "message": "usage info",
    "description": "delete a single entry or multiple entries from a table",
    "/delete": "returns a list of existing tables",
    "/delete/<table>": "returns all rows in a table",
    "/delete/<table>/<column_name>/<column_value>/../..": "query rows matching [name='value', ...]",
    "/delete/<table>/filter/<filter_string>": "query rows with filter (create_time > '2022-03-30')",
    "/delete/<table>/<column_name>/<column_value>/../filter/<filter_string>": "use query and filter"
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
