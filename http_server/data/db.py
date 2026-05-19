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

BAND_ADD = """
    INSERT INTO bands
        (name, leader, created_by)
    VALUES
        (?, ?, ?);
"""

BAND_BY_NAME = """
    SELECT bands.id AS id,
           bands.name AS name,
           u2.name AS leader,
           u1.name AS created_by,
           datetime(bands.created_ts, 'unixepoch', 'localtime') AS created_ts,
           datetime(bands.updated_ts, 'unixepoch', 'localtime') AS updated_ts
    FROM bands
    JOIN users u1
      ON u1.id = bands.created_by
    JOIN users u2
      ON u2.id = bands.leader
    WHERE bands.name = ?;
"""

BAND_COUNT_CREATED = """
    SELECT COUNT(*) as count
    FROM bands
    WHERE created_by = ?;
"""

BANDS_ALL = """
    SELECT bands.id AS id,
           bands.name AS name,
           u2.name AS leader,
           u1.name AS created_by,
           datetime(bands.created_ts, 'unixepoch', 'localtime') AS created_ts,
           datetime(bands.updated_ts, 'unixepoch', 'localtime') AS updated_ts
    FROM bands
    JOIN users u1
      ON u1.id = bands.created_by
    JOIN users u2
      ON u2.id = bands.leader;
"""

MEMBER_ADD = """
    INSERT INTO band_members
        (band_id, user_id)
    VALUES
        ((SELECT id FROM bands WHERE name = ?), ?);
"""

BAND_BY_MEMBER = """
    SELECT bands.id AS id,
           bands.name AS name,
           u2.name AS leader,
           u1.name AS created_by,
           datetime(bands.created_ts, 'unixepoch', 'localtime') AS created_ts,
           datetime(bands.updated_ts, 'unixepoch', 'localtime') AS updated_ts
    FROM bands
    JOIN users u1
      ON u1.id = bands.created_by
    JOIN users u2
      ON u2.id = bands.leader
    JOIN band_members bm
      ON bm.band_id = bands.id
    WHERE bm.user_id = ?;
"""

async def init() -> bool:
    global DB_NAME
    DB_NAME = Path(os.path.dirname(__file__), os.environ.get("DB_NAME"))
    try:
        if not os.path.exists(DB_NAME):
            schema_file = Path(os.path.dirname(__file__), "playlist_schema.sql")
            with open(schema_file, "r", encoding="utf-8") as f:
                schema_file = f.read()
            async with asql.connect(DB_NAME, autocommit=True) as db:
                await db.executescript(schema_file)
            LOGGER.info(f"DB created at '{DB_NAME}'!")
        else:
            LOGGER.info(f"DB found at '{DB_NAME}'!")

        db_health = await health()
        if not db_health:
            return False
        return True
    except Exception as ex:
        LOGGER.error(f"Failed to create db file at '{DB_NAME}': {ex}")
        return False

async def health():
    try:
        async with asql.connect(DB_NAME) as db:
            await db.execute("SELECT 1")
            await db.execute("PRAGMA integrity_check")
        return True
    except Exception as ex:
        print(f"DB health check failed: {ex}")
        return False

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

async def executetransaction(query: list[str], data: list[tuple]=None) -> list | int:
    global DB_NAME
    results = None
    async with asql.connect(DB_NAME, autocommit=True) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        db.row_factory = asql.Row
        for q,d in zip(query, data):
            async with db.execute(q, d) as cursor:
                if cursor.rowcount == -1:
                    results = await cursor.fetchall()
                else:
                    results = cursor.rowcount
    return results

async def userExists(user_name: str) -> bool:
    global USER_EXISTS
    result = await execute(USER_EXISTS, (user_name,))
    return result[0]["count"] == 1

async def userAdd(user_name: str, password: str) -> int:
    global USER_ADD
    await execute(USER_ADD, (user_name, password))

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

async def bandAdd(band_name: str, user_id: int) -> int:
    global BAND_ADD, MEMBER_ADD
    await executetransaction([BAND_ADD, MEMBER_ADD], [(band_name, user_id, user_id), (band_name, user_id)])

async def bandByName(band_name: str) -> list:
    global BAND_BY_NAME
    return await execute(BAND_BY_NAME, (band_name,))

async def bandCountCreated(user_id: int) -> list:
    global BAND_COUNT_CREATED
    return await execute(BAND_COUNT_CREATED, (user_id,))

async def bandsAll() -> list:
    global BANDS_ALL
    return await execute(BANDS_ALL)

async def bandByMember(user_id: int) -> bool:
    global BAND_BY_MEMBER
    return await execute(BAND_BY_MEMBER, (user_id,))
