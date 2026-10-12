from setuptools import setup, find_packages

setup(
    name="tokenshield",
    version="1.0.0",
    description="Multi-Modal Pre-Inference Optimization Gateway for LLMs & Vision APIs",
    author="Harshit Pratap",
    packages=find_packages(),
    py_modules=["cli", "gateway", "mcp_server", "proxy_server", "api_server", "universal_agent_api", "auto_setup"],
    install_requires=[
        "Pillow>=10.0.0",
        "mcp>=1.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "httpx>=0.25.0",
        "pydantic>=2.0.0"
    ],
    entry_points={
        "console_scripts": [
            "tokenshield = mcp_server:main",
            "tokenshield-mcp = mcp_server:main",
            "tokenshield-sse = mcp_server:run_sse",
            "tokenshield-cli = cli:main",
            "tokenshield-api = api_server:start_api",
            "tokenshield-agent-api = universal_agent_api:start_universal_api",
            "tokenshield-proxy = proxy_server:start_server",
        ],
    },
)
