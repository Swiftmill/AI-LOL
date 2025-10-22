@echo off
py -3.11 -m pip install --upgrade pyinstaller
py -3.11 -m PyInstaller --noconfirm --onefile --name "MyLocalAI" app.py
echo Build OK: dist\MyLocalAI.exe
