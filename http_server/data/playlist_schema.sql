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

----------------------------------------------------------------
-- BANDS -------------------------------------------------------
----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS bands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(64) UNIQUE NOT NULL,
    leader     INTEGER NOT NULL,
    created_by INTEGER NOT NULL,
    created_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    FOREIGN KEY (leader) REFERENCES users(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TRIGGER IF NOT EXISTS updated_ts_bands
AFTER UPDATE ON bands
FOR EACH ROW
BEGIN
    UPDATE bands
    SET updated_ts = (strftime('%s', 'now'))
    WHERE id = OLD.id;
END;

----------------------------------------------------------------
-- BAND MEMBERS ------------------------------------------------
----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS band_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    band_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    created_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_ts INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    CONSTRAINT unq UNIQUE (band_id, user_id)
    FOREIGN KEY (band_id) REFERENCES bands(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TRIGGER IF NOT EXISTS updated_ts_band_members
AFTER UPDATE ON band_members
FOR EACH ROW
BEGIN
    UPDATE band_members
    SET updated_ts = (strftime('%s', 'now'))
    WHERE id = OLD.id;
END;
