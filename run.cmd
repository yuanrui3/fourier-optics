@echo off
setlocal
pushd "%~dp0"
set "fourierPython=C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1112-611-0_26.1112.611.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe"
if not exist "%fourierPython%" set "fourierPython=python"
if "%~1"=="" (
    "%fourierPython%" -B -m fourierbench gate1
) else (
    "%fourierPython%" -B -m fourierbench %*
)
set "fourierExit=%errorlevel%"
popd
exit /b %fourierExit%
