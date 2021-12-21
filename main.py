import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import sqlite3
from sqlite3 import Connection

from pydantic import BaseModel, Field

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        'http://localhost:3000',
        'http://192.168.1.92:3000',
        'http://streep.capri',
        'https://streep.capri',
        'https://capri.imabot.nl'
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


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

    res = cursor.execute('SELECT DISTINCT who FROM ledger GROUP BY who').fetchall()

    con.close()
    return [person[0] for person in res]


@app.get("/items")
async def persons():
    con = get_db()
    cursor = con.cursor()

    res = cursor.execute('SELECT what FROM ledger GROUP BY what').fetchall()

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
