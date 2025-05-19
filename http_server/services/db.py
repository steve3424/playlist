import logging
import os
import aiosqlite as asql
from pathlib import Path

LOGGER = logging.getLogger(f"playlist.{__name__}")
DB_NAME = None

USER_EXISTS = """
    SELECT COUNT(*) as count
    FROM users
    WHERE name = ?;
"""

USER_ADD = """
    INSERT INTO users
        (name, password)
    VALUES
        (?, ?);
"""

def init():
    global DB_NAME
    DB_NAME = Path(os.path.dirname(__file__), os.pardir, "data", os.environ.get("DB_NAME"))

async def execute(query: str, data: tuple) -> list | int:
    global DB_NAME
    async with asql.connect(DB_NAME, autocommit=True) as db:
        db.row_factory = asql.Row
        async with db.execute(query, data) as cursor:
            if cursor.rowcount == -1:
                return await cursor.fetchall()
            else:
                return cursor.rowcount

async def userExists(user_name: str) -> bool:
    global USER_EXISTS
    result = await execute(USER_EXISTS, (user_name,))
    return result[0]["count"] == 1

async def userAdd(user_name: str, password: str) -> int:
    global USER_ADD
    result = await execute(USER_ADD, (user_name, password))
    if result != 1:
        raise Exception(f"Error adding user. Rows affected is {result}!")
