@echo off
TITLE TokenShield 1-Click Automatic Setup
COLOR 0B
echo =================================================================
echo   [TOKENSHIELD] 1-CLICK UNIVERSAL AUTOMATIC INSTALLER
echo =================================================================
echo.
echo [1/3] Checking Python runtime...
python --version
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

echo.
echo [2/3] Installing required libraries (Pillow, MCP, FastAPI, Uvicorn)...
pip install -q Pillow mcp fastapi uvicorn

echo.
echo [3/3] Automatically configuring Claude Desktop / Cursor...
python auto_setup.py

echo.
echo =================================================================
echo   RUNNING VERIFICATION BENCHMARK...
echo =================================================================
python demo_test.py

echo.
echo =================================================================
echo   ALL ENGINES CONFIGURED & VERIFIED SUCCESSFULLY!
echo =================================================================
echo.
echo How to use right now:
echo   1. Claude Desktop: Restart Claude, TokenShield is already linked!
echo   2. Run Proxy Server: python proxy_server.py
echo   3. CLI Optimizer:    python cli.py --text "your prompt"
echo.
pause
