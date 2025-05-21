----------------------------------------------------------------
---------------------------- USERS -----------------------------
----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name VARCHAR(64) NOT NULL,
    password VARCHAR(80) NOT NULL,
    created_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TRIGGER IF NOT EXISTS updated_ts_users
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users
    SET updated_ts = (strftime('%s', 'now'))
    WHERE id = OLD.id;
END;

----------------------------------------------------------------
---------------------------- ROLES -----------------------------
----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY,
    name VARCHAR(16) UNIQUE NOT NULL,
    created_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TRIGGER IF NOT EXISTS updated_ts_roles
AFTER UPDATE ON roles
FOR EACH ROW
BEGIN
    UPDATE roles
    SET updated_ts = (strftime('%s', 'now'))
    WHERE id = OLD.id;
END;

-- NOTE: This much match http_server enum values!!
INSERT OR IGNORE INTO roles
    (id, name)
VALUES
    (0, 'user'),
    (1, 'admin');
