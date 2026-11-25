@echo off
setlocal
pushd "%~dp0"
set "fourierResearchPython=C:\Program Files\WindowsApps\OpenAI.CodexPrimaryRuntime.v26-1112-611-0_26.1112.611.0_x64__3k8sg7r9htsxt\dependencies\python\python.exe"
if not exist "%fourierResearchPython%" set "fourierResearchPython=python"
"%fourierResearchPython%" -B research\math_audit.py
set "fourierResearchExit=%errorlevel%"
if not "%fourierResearchExit%"=="0" goto researchDone
"%fourierResearchPython%" -B research\build_report.py
set "fourierResearchExit=%errorlevel%"
:researchDone
popd
exit /b %fourierResearchExit%
