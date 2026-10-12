"""
TokenShield 1-Click Universal Auto-Setup
Automatically detects OS, finds Claude Desktop / Cursor configuration files,
and injects TokenShield MCP server without any manual JSON editing!

Usage:
  python auto_setup.py
"""
import os
import sys
import json
import platform

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_SERVER_PATH = os.path.join(BASE_DIR, "mcp_server.py")
PYTHON_EXE = sys.executable

def get_claude_config_path() -> str:
    """Finds the platform-specific path to Claude Desktop configuration."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA", os.path.expanduser("~\\AppData\\Roaming"))
        return os.path.join(appdata, "Claude", "claude_desktop_config.json")
    elif system == "Darwin": # macOS
        return os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json")
    else: # Linux
        return os.path.expanduser("~/.config/Claude/claude_desktop_config.json")

def auto_configure_claude():
    print("="*65)
    print("⚡ TOKENSHIELD 1-CLICK AUTOMATIC MCP INSTALLER")
    print("="*65)

    config_path = get_claude_config_path()
    config_dir = os.path.dirname(config_path)
    os.makedirs(config_dir, exist_ok=True)

    print(f"Detecting Operating System : {platform.system()} ({platform.release()})")
    print(f"Target Config File         : {config_path}")
    print(f"TokenShield Server Path    : {MCP_SERVER_PATH}")
    print(f"Python Runtime             : {PYTHON_EXE}")

    config_data = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            print("Found existing Claude Desktop configuration. Merging...")
        except Exception as e:
            print(f"Note: Creating fresh config (could not parse existing: {e})")
            config_data = {}

    if "mcpServers" not in config_data:
        config_data["mcpServers"] = {}

    # Inject TokenShield
    config_data["mcpServers"]["tokenshield"] = {
        "command": PYTHON_EXE,
        "args": [MCP_SERVER_PATH]
    }

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        print("\n✅ SUCCESS: TokenShield MCP Server automatically registered in Claude Desktop!")
        print("👉 Action Required: Simply restart Claude Desktop, and TokenShield will be active!")
    except Exception as e:
        print(f"\n❌ Error writing config file: {e}")

    print("="*65)

if __name__ == "__main__":
    auto_configure_claude()
