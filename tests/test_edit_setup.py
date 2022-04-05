# coding: utf-8
from db_functions import *
import sqlite3

# -- setup --
class Request(object):
    def __init__(self):
        self.params = {}
        self.params["filter"] = 'user_id > "3"'
        self.params["heart_rate"] = 70
        self.params["blood_o2"] = "95"
        self.params["temperature"] = 98.2
        # self.params["username"] = "user_01"
        # self.params["password"] = "user_01"


db = sqlite3.connect("m2band.db", detect_types=1)
db.row_factory = sqlite3.Row
request = Request()
table = "oximeter"
url_paths = ""


# params = {"heart_rate": 112, "blood_o2": 98, "temperature": 91.0}
# params["filter"] = "user_id = 4"

all_columns = getColumns(db, table)
editable_columns = getColumns(db, table, all_columns, required=True)
non_edit_columns = getColumns(db, table, all_columns, non_editable=True)
params, filters = parseUrlPaths(url_paths, request.params, all_columns)

# -- at least 1 edit parameter required
if not any(k in params.keys() for k in editable_columns):
    res = {
        "message": "missing edit parameter",
        "editable": editable_columns,
        "supplied": params,
    }
    print(clean(res))

# -- at least 1 query parameter required
query_params = non_edit_columns + ["filter"]
if not any(k in request.params.keys() for k in query_params):
    res = {
        "message": "missing query parameter",
        "query_params": query_params,
        "supplied": params,
    }
    print(clean(res))

# -- define "columns" to edit and "values" to insert (parsed from params in HTTP request)
columns = [column for column in editable_columns if params.get(column)]
col_values = [params[column] for column in columns]

# -- build "conditions" string and "values" string/array for "updateRow()"
conditions = " AND ".join(
    [f"{param}=?" for param in non_edit_columns if params.get(param)]
)
values = [params[param] for param in non_edit_columns if params.get(param)]
if filters:
    conditions, values = parseFilters(filters, conditions, values)

# -- query database -- UPDATE users SET username=? WHERE (user_id=?);
args = {
    "table": table,
    "columns": columns,
    "col_values": col_values,
    "where": conditions,
    "values": values,
}


data = {
    "all_columns": all_columns,
    "editable_columns": editable_columns,
    "non_edit_columns": non_edit_columns,
    "params": params,
    "filters": filters,
    "query_params": query_params,
    "columns": columns,
    "col_values": col_values,
    "where": conditions,
    "values": values,
}
print(data)
