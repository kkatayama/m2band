# coding: utf-8
from pathlib import Path
import sys

sys.path.append(str(Path(".").absolute().parent))
from random import randint
from rich import print
from db_functions import *
import sqlite3


def get(db, table):
    return fetchRows(db, table=table)


def add(db, table, columns, col_values):
    col_id = insertRow(db, table=table, columns=columns, col_values=col_values)
    print({"col_id": col_id, "columns": columns, "col_values": col_values})


def createTable(db, table, url_paths):
    params, columns = mapUrlPaths(url_paths, {}, table)
    res = addTable(db, table=table, columns=columns)
    res.update({"table": table})
    print(res)


def dropTable(db, table):
    res = deleteTable(db, table=table)
    res.update({"table": table})
    print(res)


if __name__ == "__main__":
    db = sqlite3.connect("../m2band.db")
    db.text_factory = str
    db.row_factory = sqlite3.Row

    # -- store existing table data
    oximeter = get(db, table="oximeter")
    print("EXISTING TABLES:")
    print(f'"oximeter" = {oximeter}')
    print()

    # -- delete existing tables
    print("DELETE TABLES:")
    dropTable(db, table="oximeter")
    print()

    # -- create tables
    print("CREATE TABLES:")
    createTable(
        db,
        table="oximeter",
        url_paths="entry_id/INTEGER/user_id/INTEGER/heart_rate/INTEGER/blood_o2/INTEGER/temperature/DOUBLE/steps/INTEGER/entry_time/DATETIME",
    )
    print()

    # -- insert data to tables:
    print("INSERT DATA:")
    for item in oximeter:
        item["steps"] = randint(0, 10)
        required = ["user_id", "heart_rate", "blood_o2", "temperature", "steps"]
        entry = {k: item[k] for k in required}
        columns, col_values = list(entry.keys()), list(entry.values())
        add(db, table="oximeter", columns=columns, col_values=col_values)
    db.commit()
