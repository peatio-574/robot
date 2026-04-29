chcp 65001
@echo off
cd /d "%~dp0"
echo "安装python库"
..\python3.10\python.exe -m pip install -r ../resources/requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com
echo "安装浏览器驱动"
..\python3.10\python.exe -m playwright install
pause