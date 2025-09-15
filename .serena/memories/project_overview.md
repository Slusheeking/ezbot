# EzBot Project Overview

## Project Purpose
EzBot is a Python-based project that integrates MCP (Model Context Protocol) servers for extended functionality. The project currently focuses on financial data integration through the Polygon API MCP server.

## Tech Stack
- **Python**: Primary language (>=3.10)
- **MCP**: Model Context Protocol for extensible tools and resources
- **Polygon API**: Financial data integration
- **GitHub Actions**: CI/CD with Claude Code integration
- **uv**: Modern Python package management
- **Ruff**: Linting and formatting

## Project Structure
```
ezbot/
├── README.md                           # Project documentation
├── package-lock.json                   # Node.js dependencies (minimal)
├── mcp/                                # MCP servers directory
│   └── mcp_polygon/                    # Polygon API MCP server
│       ├── src/mcp_polygon/
│       │   ├── server.py               # Main MCP server implementation
│       │   └── __init__.py
│       ├── entrypoint.py               # Server startup logic
│       ├── pyproject.toml              # Python project configuration
│       └── README.md
├── .github/workflows/
│   ├── claude.yml                      # Claude Code GitHub Action
│   └── schedule-claude.yml             # Scheduled Claude tasks
└── .serena/                            # Serena tool configuration
```

## Key Components
- **MCP Polygon Server**: Comprehensive financial data API with 50+ tools for market data, stocks, crypto, futures
- **GitHub Actions Integration**: Automated Claude Code workflows
- **Modular Architecture**: Transitioned from monolithic to MCP-based extensible design