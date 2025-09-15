# Suggested Commands for EzBot Development

## Python/MCP Development
```bash
# Navigate to MCP server directory
cd mcp/mcp_polygon

# Install dependencies with uv
uv sync

# Run MCP server locally for testing
python entrypoint.py

# Run with specific transport
MCP_TRANSPORT=stdio python entrypoint.py

# Lint code with ruff
uv run ruff check .
uv run ruff format .
```

## Git Operations
```bash
# Standard git workflow
git status
git add -A
git commit -m "message"
git push origin main
```

## Claude Code Integration
```bash
# Manual MCP server registration (if not using FastMCP)
claude mcp add polygon-server -- uv run --project mcp/mcp_polygon python entrypoint.py

# List registered MCP servers
claude mcp list

# Remove MCP server
claude mcp remove polygon-server
```

## Environment Setup
```bash
# Set Polygon API key for development
export POLYGON_API_KEY=your_api_key_here

# Or create .env file in mcp/mcp_polygon/
echo "POLYGON_API_KEY=your_api_key" > mcp/mcp_polygon/.env
```

## Docker Operations (if using containerized deployment)
```bash
cd mcp/mcp_polygon
docker-compose up -d
docker-compose logs -f
```