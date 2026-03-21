@echo off

REM Path to Git Bash
set GIT_BASH="C:\Program Files\Git\git-bash.exe"

REM ==============================
REM FRONTEND
REM ==============================
start "Frontend" %GIT_BASH% -c "cd /f/scopia/frontend; npm run dev & sleep 3; exec bash"

REM ==============================
REM DATABASE (psql with password)
REM ==============================
start "Database" %GIT_BASH% -c "export PGPASSWORD=poostgrees; psql -U postgres -d forensic_db; exec bash"

REM ==============================
REM BACKEND
REM ==============================
start "Backend" %GIT_BASH% -c "cd /f/scopia/backend; mvn spring-boot:run; exec bash"

REM ==============================
REM ROOT TERMINAL
REM ==============================
start "Root" %GIT_BASH% -c "cd /f/scopia; exec bash"

REM ==============================
REM OPEN APP
REM ==============================
start "Frontend" %GIT_BASH% -c "cd /f/scopia/frontend; npm run dev & explorer http://localhost:5173/login; exec bash"