@echo off
setlocal enabledelayedexpansion

for /f "tokens=*" %%a in ('git rev-parse --show-toplevel 2^>nul') do set root=%%a
if not defined root set root=?

for %%i in (!root!) do set repo=%%~nxi

for /f "tokens=*" %%a in ('git remote get-url origin 2^>nul') do set remote=%%a
if not defined remote set remote=no-remote

for /f "tokens=*" %%a in ('git rev-parse --abbrev-ref HEAD 2^>nul') do set branch=%%a
if not defined branch set branch=?

rem Extract host from remote URL (simplified for Windows)
set host=!remote!
set host=!host:*@=!
for /f "tokens=1 delims=:/" %%a in ("!host!") do set host=%%a

for /f "tokens=*" %%a in ('git config user.email 2^>nul') do set email=%%a
if not defined email set email=?

echo 📦 !repo!  🌿 !branch!  🔗 !remote!  🏷 host=!host!  ✉ !email!