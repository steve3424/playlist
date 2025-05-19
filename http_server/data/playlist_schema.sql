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

CREATE TRIGGER updated_ts
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users
    SET updated_ts = (strftime('%s', 'now'))
    WHERE id = OLD.id;
END;
