@echo off
cd /d "%~dp0"
echo Executando migração...
sqlite3 "../data/os_system_dev.db" ".read add_details_column.sql"
echo Migração concluída!
