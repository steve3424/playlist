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

USERS_ALL = """
    SELECT users.id AS id,
           users.name AS name,
           app_roles.name AS role,
           datetime(users.created_ts, 'unixepoch', 'localtime') AS created_ts,
           datetime(users.updated_ts, 'unixepoch', 'localtime') AS updated_ts
    FROM users
    JOIN app_roles
      ON users.role_id = app_roles.id;
"""

USER_BY_ID = """
    SELECT users.id AS id,
           users.name AS name,
           app_roles.name AS role,
           datetime(users.created_ts, 'unixepoch', 'localtime') AS created_ts,
           datetime(users.updated_ts, 'unixepoch', 'localtime') AS updated_ts
    FROM users
    JOIN app_roles
      ON users.role_id = app_roles.id
    WHERE users.id = ?;
"""

USER_BY_NAME = """
    SELECT users.id AS id,
           users.name AS name,
           app_roles.name AS role,
           datetime(users.created_ts, 'unixepoch', 'localtime') AS created_ts,
           datetime(users.updated_ts, 'unixepoch', 'localtime') AS updated_ts
    FROM users
    JOIN app_roles
      ON users.role_id = app_roles.id
    WHERE users.name = ?;
"""

USER_PASSWORD_BY_NAME = """
    SELECT users.id AS id,
           users.name AS name,
           users.password AS password,
           app_roles.name AS role,
           datetime(users.created_ts, 'unixepoch', 'localtime') AS created_ts,
           datetime(users.updated_ts, 'unixepoch', 'localtime') AS updated_ts
    FROM users
    JOIN app_roles
      ON users.role_id = app_roles.id
    WHERE users.name = ?;
"""

DELETE_USER = """
    DELETE FROM users
    WHERE name = ?;
"""

def init():
    global DB_NAME
    DB_NAME = Path(os.path.dirname(__file__), os.pardir, "data", os.environ.get("DB_NAME"))

async def execute(query: str, data: tuple=None) -> list | int:
    global DB_NAME
    async with asql.connect(DB_NAME, autocommit=True) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
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

async def usersAll() -> list:
    global USERS_ALL
    return await execute(USERS_ALL)

async def userById(id: int) -> list:
    global USER_BY_ID
    return await execute(USER_BY_ID, (id,))

async def userByName(name: str) -> list:
    global USER_BY_NAME
    return await execute(USER_BY_NAME, (name,))

async def userAndPasswordByName(name: str) -> list:
    global USER_PASSWORD_BY_NAME
    return await execute(USER_PASSWORD_BY_NAME, (name,))

async def deleteUser(name: str) -> int:
    global DELETE_USER
    return await execute(DELETE_USER, (name,))
