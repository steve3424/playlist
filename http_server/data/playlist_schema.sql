----------------------------------------------------------------
-- USERS -------------------------------------------------------
----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) UNIQUE NOT NULL,
    password VARCHAR(80) NOT NULL,
    role_id INTEGER NOT NULL DEFAULT 0,
    created_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (role_id) REFERENCES app_roles(id)
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
-- APP_ROLES ---------------------------------------------------
----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS app_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(16) UNIQUE NOT NULL,
    created_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

CREATE TRIGGER IF NOT EXISTS updated_ts_roles
AFTER UPDATE ON app_roles
FOR EACH ROW
BEGIN
    UPDATE app_roles
    SET updated_ts = (strftime('%s', 'now'))
    WHERE id = OLD.id;
END;

-- NOTE: This much match http_server enum values!!
INSERT OR IGNORE INTO app_roles
    (id, name)
VALUES
    (0, 'user'),
    (1, 'admin');
