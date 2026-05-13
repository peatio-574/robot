chcp 65001
@echo off
cd /d "%~dp0"
D:\robot\python3.10\python.exe -m pip uninstall greenlet -y
D:\robot\python3.10\python.exe -m pip install greenlet
pause