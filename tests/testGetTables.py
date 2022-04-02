# coding: utf-8
from db_functions import *
import sqlite3

db = sqlite3.connect("m2band.db", detect_types=1)
db.row_factory = sqlite3.Row
tables = getTables(db)
for table in tables:
    columns = getColumns(db, table["name"])
    sql = table.pop("sql")
    text = (
        f"""(?P<name>({"|".join(columns)})) (?P<type>([mdfA-Z\(\)\'\"\_\-.\:%\s]*))"""
    )
    regex = r"{}".format(text)
    r = re.compile(regex)
    table["columns"] = [m.groupdict() for m in r.finditer(sql)]
    table["columns"][-1]["type"] = table["columns"][-1]["type"] + re.search(
        r"(?P<end>, 'NOW'(.*))", sql
    ).groupdict().get("end")
db.close()
print(tables)
