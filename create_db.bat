@echo off

IF "%~1" == "" (
    echo Please specify db name!
) ELSE (
    SETLOCAL EnableDelayedExpansion
    SET DB_NAME=http_server\data\playlist_%1.db
    sqlite3 !DB_NAME! < http_server\data\playlist_schema.sql
    echo Created db at '!DB_NAME!'!
)
