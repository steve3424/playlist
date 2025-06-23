@echo off

sqlite3 http_server\data\playlist_%1.db < http_server\data\playlist_schema.sql
