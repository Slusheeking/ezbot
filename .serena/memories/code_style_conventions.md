# Code Style and Conventions

## Python Style Guidelines
- **Python Version**: >=3.10 required
- **Linting**: Ruff for code quality and formatting
- **Type Hints**: Use type annotations (evident in entrypoint.py with Literal types)
- **Docstrings**: Function documentation for MCP tools (seen in server.py)

## MCP Server Conventions
- **Server Naming**: Use descriptive names (e.g., "polygon_mcp", "Polygon MCP Server")  
- **Tool Functions**: Each MCP tool should have clear docstrings describing parameters and purpose
- **Environment Variables**: Use environment variables for API keys and configuration
- **Transport Support**: Support multiple transport types (stdio, sse, streamable-http)

## Project Structure Patterns
- **Modular Design**: Separate MCP servers in dedicated directories under `mcp/`
- **Entry Points**: Use `entrypoint.py` for server startup logic
- **Configuration**: Use `pyproject.toml` for Python project metadata and dependencies
- **GitHub Actions**: Integrate Claude Code workflows for automated assistance

## Dependency Management
- **Primary**: Use `uv` for Python package management
- **Lock Files**: Maintain `uv.lock` for reproducible builds
- **Dev Dependencies**: Separate development dependencies in `pyproject.toml`

## Environment Configuration
- **API Keys**: Never commit API keys, use environment variables
- **Transport Selection**: Support configurable transport via MCP_TRANSPORT environment variable
- **Error Handling**: Graceful handling of missing environment variables with warnings