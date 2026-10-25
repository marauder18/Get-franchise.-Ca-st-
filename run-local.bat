@echo off
setlocal
title Getfranchise Local Preview
cd /d "%~dp0GetfranchiseAi"

if errorlevel 1 (
  echo Could not open the GetfranchiseAi folder.
  pause
  exit /b 1
)

set "NODE_EXE="
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe" (
  set "NODE_EXE=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
) else (
  where node >nul 2>nul
  if not errorlevel 1 set "NODE_EXE=node"
)

if "%NODE_EXE%"=="" (
  echo Node.js was not found.
  echo Install Node.js from https://nodejs.org/ or run this project from a Codex session that includes the bundled runtime.
  pause
  exit /b 1
)

"%NODE_EXE%" preview-server.mjs
pause
