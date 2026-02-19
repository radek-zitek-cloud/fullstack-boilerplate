# Serena Project - Full-Stack Boilerplate

This project is configured for Serena MCP with full code-aware capabilities for both Python (FastAPI backend) and TypeScript/React (frontend).

## Quick Start

```bash
# Start Serena MCP server
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --project /home/radek/Code/oclab/fullstack-boilerplate
```

## Project Structure

- **Backend** (`backend/`): Python, FastAPI, SQLAlchemy
- **Frontend** (`frontend/src/`): TypeScript, React, Vite
- **Database**: SQLite in `data/`
- **Uploads**: User files in `uploads/`
- **Logs**: Application logs in `logs/`

## Serena Capabilities Enabled

- **Python**: Code navigation, symbol search, refactoring, diagnostics
- **TypeScript**: Code navigation, symbol search, auto-imports, diagnostics
- **Cross-language**: Project-wide search and understanding

## Useful Commands

Once activated, you can use:
- `serena_read_file` - Read files with code awareness
- `serena_find_symbol` - Find symbols across the codebase
- `serena_grep` - Search with AST awareness
- `serena_list_dir` - List directories
- `serena_replace_content` - Edit files safely
