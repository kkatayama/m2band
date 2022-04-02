# coding: utf-8
from db_functions import *
import sqlite3


def testGetColumns(table):
    params = {"user_id": 4, "heart_rate": 112, "blood_o2": 98, "temperature": 91.0}

    db = sqlite3.connect("m2band.db", detect_types=1)
    all_columns = getColumns(db, table)
    required_columns = getColumns(db, table, required=True)
    col_ref = getColumns(db, table, ref=True)

    print(f"table = '{table}'")
    print(f"all_columns: {all_columns}")
    print(f"required_columns: {required_columns}")
    print(f"col_ref: '{col_ref}'")

    col_id = 4 if table == "users" else 21
    col_ref = getColumns(db, table, ref=True)
    res = {"message": f"data added to <{table}>", col_ref: col_id}
    for r in re.findall(r"(.*_id)", " ".join(required_columns)):
        res[r] = params.get(r)
    print(res)
    print()
    db.commit()
    db.close()


for table in ["users", "oximeter"]:
    testGetColumns(table)
