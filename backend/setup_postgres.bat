@echo off
echo ========================================
echo FarmConnect PostgreSQL Setup
echo ========================================

REM Stop PostgreSQL
net stop postgresql-x64-18

REM Enable trust authentication
(
echo # TYPE  DATABASE        USER            ADDRESS                 METHOD
echo local   all             all                                     trust
echo host    all             all             127.0.0.1/32            trust
echo host    all             all             ::1/128                 trust
) > "C:\Program Files\PostgreSQL\18\data\pg_hba.conf"

REM Start PostgreSQL
net start postgresql-x64-18

echo Waiting for PostgreSQL...
timeout /t 3

REM Create database and user with your password
echo Creating farmconnect_user and database...
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d postgres -c "CREATE USER farmconnect_user WITH PASSWORD '56451051';"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d postgres -c "CREATE DATABASE farmconnect_db OWNER farmconnect_user;"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d postgres -c "GRANT ALL PRIVILEGES ON DATABASE farmconnect_db TO farmconnect_user;"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d farmconnect_db -c "GRANT ALL ON SCHEMA public TO farmconnect_user;"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d farmconnect_db -c "ALTER SCHEMA public OWNER TO farmconnect_user;"
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -d farmconnect_db -c "ALTER USER farmconnect_user WITH SUPERUSER;"

echo ========================================
echo Database created successfully!
echo ========================================

REM Revert to secure authentication
(
echo # TYPE  DATABASE        USER            ADDRESS                 METHOD
echo local   all             all                                     scram-sha-256
echo host    all             all             127.0.0.1/32            scram-sha-256
echo host    all             all             ::1/128                 scram-sha-256
) > "C:\Program Files\PostgreSQL\18\data\pg_hba.conf"

REM Restart PostgreSQL
net stop postgresql-x64-18
net start postgresql-x64-18

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Connection details:
echo   Host: localhost
echo   Port: 5432
echo   Database: farmconnect_db
echo   User: farmconnect_user
echo   Password: 56451051
echo.
echo Now run: python test_db.py
pause