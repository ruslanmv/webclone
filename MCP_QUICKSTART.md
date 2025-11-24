# 🤖 WebClone MCP Server - 2-Minute Quick Start

## What is This?

WebClone is now an **official MCP (Model Context Protocol) server** that lets AI agents like Claude download websites and files!

---

## Installation (One Time)

```bash
# Install WebClone with MCP support
make install-mcp
```

That's it! Installation complete.

---

## Usage

### Option 1: With Claude Desktop (Recommended)

1. **Add to Claude's config**:

   Edit `~/.config/claude/claude_desktop_config.json`:

   ```json
   {
     "mcpServers": {
       "webclone": {
         "command": "python",
         "args": ["/absolute/path/to/webclone/webclone-mcp.py"]
       }
     }
   }
   ```

   💡 Replace `/absolute/path/to/webclone/` with your actual path!

2. **Restart Claude Desktop**

3. **Use it!**

   Ask Claude:
   ```
   Clone the FastAPI documentation website
   ```

   Claude will use WebClone to download it automatically! 🎉

### Option 2: Standalone Server

```bash
# Run MCP server on stdio
make mcp
```

---

## Available Tools for AI Agents

Your AI agent can now:

| Tool | What It Does |
|------|--------------|
| **clone_website** | Download entire websites with all pages & assets |
| **download_file** | Download a specific file or URL |
| **save_authentication** | Guide for saving login cookies |
| **list_saved_sessions** | List all saved authentication sessions |
| **get_site_info** | Get website metadata without downloading |

---

## Example Conversations with Claude

### Example 1: Simple Clone

```
You: Clone https://example.com

Claude: I'll clone that website for you.
[Uses clone_website tool]

✅ Success! Cloned 5 pages, 12 assets, 2.3 MB total.
Output directory: ./website_mirror
```

### Example 2: With Limits

```
You: Clone https://docs.python.org but limit it to 50 pages

Claude: I'll clone the Python docs with a 50-page limit.
[Uses clone_website with max_pages=50]

✅ Cloned 50 pages, 234 assets, 15.8 MB.
```

### Example 3: Download Specific File

```
You: Download the PDF from https://example.com/report.pdf

Claude: I'll download that PDF for you.
[Uses download_file tool]

✅ Downloaded to ./downloads/
```

---

## Authentication (Optional)

For sites requiring login (Google Drive, GitHub, etc.):

1. **Create session using GUI**:
   ```bash
   make gui
   ```

2. **Go to "🔐 Authentication"** tab

3. **Save your session** (e.g., "google_drive")

4. **Use in Claude**:
   ```
   Clone my Google Drive folder using the google_drive session
   ```

   Claude will automatically use your saved cookies! 🔐

---

## Integration with CrewAI

```python
from crewai import Agent, Task, Crew

# WebClone tool automatically available via MCP

researcher = Agent(
    role='Web Archiver',
    goal='Clone documentation sites',
    tools=['clone_website'],  # MCP tool
    verbose=True
)

task = Task(
    description='Clone https://fastapi.tiangolo.com',
    agent=researcher
)

crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

---

## Troubleshooting

### Claude can't see WebClone tools

1. ✅ Check config file path is correct
2. ✅ Use **absolute** paths (not relative)
3. ✅ Restart Claude Desktop completely
4. ✅ Ask Claude: "What tools do you have?"

### MCP server won't start

```bash
# Reinstall
make install-mcp

# Test
python webclone-mcp.py
```

### Downloads fail

1. ✅ Check URL is valid (`http://` or `https://`)
2. ✅ Check output directory permissions
3. ✅ For auth sites, create session first

---

## Advanced Usage

### Speed Optimization

```
Clone https://example.com with 20 workers and 50ms delay
```

### Stealth Mode

```
Clone https://example.com slowly with 3 workers and 2 second delay
```

### Get Info First

```
Get information about https://example.com before cloning
```

---

## Full Documentation

- **Complete MCP Guide**: `docs/MCP_GUIDE.md`
- **Authentication Help**: `docs/AUTHENTICATION_GUIDE.md`
- **CLI Reference**: `docs/CLI_GUIDE.md`
- **GUI Guide**: `docs/GUI_GUIDE.md`

---

## What Makes WebClone MCP Special?

✅ **Official MCP Tool** - Designed for AI agents
✅ **5 Powerful Tools** - Clone, download, authenticate, inspect
✅ **Production Ready** - Battle-tested website cloning engine
✅ **Authentication Support** - Access protected sites
✅ **Stealth Mode** - Bypass bot detection
✅ **Fast & Async** - Concurrent downloads
✅ **CrewAI Compatible** - Works with all AI frameworks

---

**That's it! AI agents can now clone websites! 🚀**

**Author**: Ruslan Magana | **Website**: ruslanmv.com
