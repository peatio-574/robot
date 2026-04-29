chcp 65001
@echo off
cd /d "%~dp0"
echo 运行Order.py
..\python3.10\python.exe ../ChangeOrder.py
pause