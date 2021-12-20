import os

from fastapi import FastAPI

import sqlite3
from sqlite3 import Connection

from pydantic import BaseModel, Field

app = FastAPI()


def get_db() -> Connection:
    return sqlite3.connect(os.getenv('DB', 'streeplijst.sqlite'))


@app.get("/")
async def balance():
    con = get_db()
    cursor = con.cursor()

    res = cursor.execute('SELECT who, what, SUM(amount) FROM ledger GROUP BY who, what')
    balance = {}
    for who, what, amount in res:
        if who not in balance:
            balance[who] = {}

        balance[who][what] = amount

    con.close()
    return balance


@app.get("/persons")
async def persons():
    con = get_db()
    cursor = con.cursor()

    res = cursor.execute('SELECT DISTINCT who FROM ledger').fetchall()

    con.close()
    return [person[0] for person in res]


@app.get("/items")
async def persons():
    con = get_db()
    cursor = con.cursor()

    res = cursor.execute('SELECT DISTINCT what FROM ledger').fetchall()

    con.close()
    return [item[0] for item in res]


class StreepModel(BaseModel):
    who: str = Field(..., max_length=255, min_length=1)
    what: str = Field(..., max_length=255, min_length=1)
    amount: int


@app.post("/")
async def streep(data: StreepModel):
    con = get_db()
    cursor = con.cursor()

    cursor.execute(
        'INSERT INTO ledger (`date`, `who`, `what`, `amount`) VALUES (datetime(), ?, ?, ?)',
        (data.who, data.what, data.amount))
    res = cursor.execute(
        'SELECT who, what, SUM(amount) FROM ledger WHERE who=? GROUP BY who, what',
        (data.who,)).fetchall()

    con.commit()
    con.close()
    return {
        "success": True,
        "new_balance": {
            what: amount
            for who, what, amount in res
        }
    }
