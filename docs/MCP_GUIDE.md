# 🤖 WebMirror MCP Server - Complete Guide

## Overview

WebMirror is now available as an **official Model Context Protocol (MCP) server**, making website cloning and file downloading capabilities available to AI agents like Claude, CrewAI, and any MCP-compatible framework.

---

## What is MCP?

**Model Context Protocol (MCP)** is an open standard that lets AI agents use external tools and services. By running WebMirror as an MCP server, AI assistants can:

- Clone entire websites
- Download specific files or URLs
- Manage authentication sessions
- Get site information before downloading
- Access saved cookies for authenticated crawling

---

## 🚀 Quick Start

### Installation

```bash
# Install WebMirror with MCP support
make install-mcp

# Or manually
pip install -e ".[mcp]"
```

### Standalone Usage

```bash
# Launch MCP server (runs on stdio)
make mcp

# Or directly
python webmirror-mcp.py
```

### Integration with Claude Desktop

1. **Install WebMirror MCP**:
   ```bash
   make install-mcp
   ```

2. **Configure Claude Desktop**:

   Edit `~/.config/claude/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

   ```json
   {
     "mcpServers": {
       "webmirror": {
         "command": "python",
         "args": ["/absolute/path/to/webmirror/webmirror-mcp.py"]
       }
     }
   }
   ```

   Replace `/absolute/path/to/webmirror/` with your actual path.

3. **Restart Claude Desktop**

4. **Verify Installation**:

   Ask Claude:
   > "What tools do you have access to?"

   Claude should mention WebMirror tools like `clone_website`, `download_file`, etc.

---

## 🔧 Available Tools

### 1. `clone_website`

Clone an entire website with all pages and assets.

**Parameters:**
- `url` (required): Website URL to clone
- `output_dir`: Output directory (default: `./website_mirror`)
- `max_pages`: Maximum pages to crawl (0 = unlimited)
- `max_depth`: Maximum link depth (0 = unlimited)
- `workers`: Concurrent workers (1-50, default: 5)
- `delay_ms`: Delay between requests in ms (default: 100)
- `include_assets`: Download CSS, JS, images (default: true)
- `same_domain_only`: Only crawl same domain (default: true)
- `cookie_file`: Path to authentication cookie file

**Example AI Request:**
```
Clone https://example-blog.com with all assets, max 50 pages
```

**Behind the Scenes:**
```json
{
  "url": "https://example-blog.com",
  "max_pages": 50,
  "include_assets": true
}
```

**Response:**
```json
{
  "status": "success",
  "url": "https://example-blog.com",
  "output_directory": "/path/to/website_mirror",
  "statistics": {
    "pages_crawled": 47,
    "assets_downloaded": 312,
    "total_size_mb": 15.42,
    "duration_seconds": 23.5
  }
}
```

---

### 2. `download_file`

Download a specific file or URL without crawling.

**Parameters:**
- `url` (required): URL to download
- `output_path`: Where to save (optional)
- `cookie_file`: Authentication cookies (optional)

**Example AI Request:**
```
Download the PDF from https://example.com/document.pdf
```

**Response:**
```json
{
  "status": "success",
  "url": "https://example.com/document.pdf",
  "output_path": "/path/to/downloads",
  "message": "Successfully downloaded..."
}
```

---

### 3. `save_authentication`

Guide for saving authentication cookies (requires manual browser interaction).

**Parameters:**
- `login_url` (required): Login page URL
- `session_name` (required): Name for this session

**Example AI Request:**
```
I need to save authentication for Google Drive
```

**Response:**
```json
{
  "status": "info",
  "message": "Authentication saving requires manual browser interaction...",
  "instructions": [
    "1. Run: make gui",
    "2. Go to Authentication Manager",
    "3. Create new session",
    "4. Use session 'google_drive' in your MCP calls"
  ]
}
```

---

### 4. `list_saved_sessions`

List all saved authentication sessions.

**Parameters:** None

**Example AI Request:**
```
Show me all saved authentication sessions
```

**Response:**
```json
{
  "status": "success",
  "sessions": [
    {
      "name": "google_work",
      "file": "./cookies/google_work.json",
      "created": 1704067200,
      "domain": ".google.com"
    },
    {
      "name": "github_personal",
      "file": "./cookies/github_personal.json",
      "created": 1704153600,
      "domain": ".github.com"
    }
  ],
  "count": 2
}
```

---

### 5. `get_site_info`

Get information about a website without downloading it.

**Parameters:**
- `url` (required): Website to analyze

**Example AI Request:**
```
Get information about https://python.org
```

**Response:**
```json
{
  "status": "success",
  "url": "https://python.org",
  "info": {
    "status_code": 200,
    "links_found": 45,
    "assets_found": 23,
    "content_type": "text/html"
  }
}
```

---

## 💡 Usage Examples

### Example 1: Clone a Documentation Site

**AI Conversation:**
```
User: Clone the Python documentation site, but limit it to 100 pages

Claude: I'll clone the Python documentation for you with a 100-page limit.
[Calls clone_website tool]

Result: Successfully cloned https://docs.python.org with 100 pages,
412 assets downloaded, total size 25.3 MB. Saved to ./website_mirror
```

---

### Example 2: Download with Authentication

**AI Conversation:**
```
User: I need to download files from my private GitHub repo

Claude: First, let's see if you have a saved GitHub session.
[Calls list_saved_sessions]

Result: I see you have "github_personal" saved. I'll use that.
[Calls clone_website with cookie_file="./cookies/github_personal.json"]

Success: Downloaded your private repo using saved authentication.
```

---

### Example 3: Get Site Info First

**AI Conversation:**
```
User: I want to clone example.com but don't know how big it is

Claude: Let me check the site first.
[Calls get_site_info]

Result: The site has 45 links and 23 assets on the homepage.
This will be a medium-sized crawl. Would you like me to proceed?

User: Yes, clone it

Claude: [Calls clone_website]
Done! Cloned 52 pages with 178 assets.
```

---

## 🔗 Integration with AI Frameworks

### CrewAI Integration

```python
from crewai import Agent, Task, Crew
from langchain.tools import Tool

# Define WebMirror tool for CrewAI
webmirror_tool = Tool(
    name="WebMirror Clone Website",
    func=lambda url: mcp_client.call_tool("clone_website", {"url": url}),
    description="Clone entire websites for offline access or data extraction"
)

# Create specialized agent
researcher = Agent(
    role='Web Researcher',
    goal='Clone and archive important documentation sites',
    backstory='Expert at preserving web content',
    tools=[webmirror_tool],
    verbose=True
)

# Define task
task = Task(
    description='Clone the FastAPI documentation site',
    agent=researcher
)

# Execute
crew = Crew(agents=[researcher], tasks=[task])
result = crew.kickoff()
```

---

### LangChain Integration

```python
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.chat_models import ChatOpenAI

# MCP tool wrapper
def clone_website_langchain(url: str) -> str:
    """Clone a website using WebMirror MCP."""
    result = mcp_client.call_tool("clone_website", {"url": url})
    return str(result)

tools = [
    Tool(
        name="CloneWebsite",
        func=clone_website_langchain,
        description="Clone entire websites with all pages and assets"
    )
]

llm = ChatOpenAI(temperature=0)
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

agent.run("Clone the React documentation website")
```

---

### Custom MCP Client

```python
import asyncio
import json
from mcp.client import Client

async def use_webmirror():
    async with Client() as client:
        # Connect to WebMirror MCP server
        await client.connect("python", ["webmirror-mcp.py"])

        # List available tools
        tools = await client.list_tools()
        print("Available tools:", tools)

        # Clone a website
        result = await client.call_tool("clone_website", {
            "url": "https://example.com",
            "max_pages": 10
        })
        print("Clone result:", json.loads(result[0].text))

asyncio.run(use_webmirror())
```

---

## 🛠️ Configuration

### Environment Variables

Create `.env` file:

```bash
# WebMirror MCP Configuration
WEBMIRROR_DEFAULT_OUTPUT_DIR=./website_mirror
WEBMIRROR_DEFAULT_WORKERS=5
WEBMIRROR_DEFAULT_DELAY_MS=100
WEBMIRROR_COOKIES_DIR=./cookies
```

### Server Configuration

The MCP server uses stdio (standard input/output) for communication, making it compatible with any MCP client.

**Server Details:**
- **Name**: `webmirror`
- **Protocol**: MCP 0.9.0+
- **Transport**: stdio
- **Tools**: 5 (clone_website, download_file, save_authentication, list_saved_sessions, get_site_info)

---

## 🔒 Security & Best Practices

### Cookie Security

1. **Never share cookie files** - they contain authentication tokens
2. **Store in ./cookies/** directory (already in .gitignore)
3. **Use dedicated accounts** for scraping
4. **Rotate sessions regularly**
5. **Delete expired cookies**

### Rate Limiting

1. **Use appropriate delays** (100-1000ms recommended)
2. **Respect robots.txt**
3. **Don't overwhelm servers**
4. **Monitor for 429 errors**

### Authentication

1. **Pre-create sessions** using GUI or CLI
2. **Reference by name** in MCP calls
3. **Test cookies** before large crawls
4. **Handle expiry gracefully**

---

## 🐛 Troubleshooting

### MCP Server Won't Start

**Problem:** ImportError when launching

**Solution:**
```bash
# Reinstall MCP dependencies
make install-mcp

# Verify installation
python -c "import mcp; print(mcp.__version__)"
```

---

### Claude Can't See Tools

**Problem:** Claude says "I don't have access to those tools"

**Solutions:**

1. **Check config path**:
   ```bash
   cat ~/.config/claude/claude_desktop_config.json
   ```

2. **Use absolute paths**:
   ```json
   {
     "mcpServers": {
       "webmirror": {
         "command": "python",
         "args": ["/Users/yourname/webmirror/webmirror-mcp.py"]
       }
     }
   }
   ```

3. **Restart Claude Desktop** completely

4. **Check logs** in Claude Desktop settings

---

### Tool Calls Fail

**Problem:** Tools return errors

**Common Causes:**

1. **Invalid URL format**
   - Must start with `http://` or `https://`

2. **Permission denied**
   - Output directory not writable

3. **Missing cookies**
   - Cookie file doesn't exist
   - Create using `make gui`

4. **Rate limiting**
   - Increase `delay_ms` parameter

---

## 📊 Performance Tips

### Optimize for Speed

```json
{
  "url": "https://example.com",
  "workers": 20,
  "delay_ms": 50,
  "include_assets": true
}
```

### Optimize for Stealth

```json
{
  "url": "https://example.com",
  "workers": 3,
  "delay_ms": 2000,
  "same_domain_only": true
}
```

### Optimize for Size

```json
{
  "url": "https://example.com",
  "include_assets": false,
  "max_pages": 100,
  "same_domain_only": true
}
```

---

## 🎯 Advanced Use Cases

### 1. Automated Documentation Backups

**Scenario:** Daily backups of your company's documentation

**CrewAI Implementation:**
```python
from crewai import Agent, Task, Crew
from datetime import datetime

backup_agent = Agent(
    role='Documentation Archiver',
    goal='Maintain daily backups of all company documentation',
    tools=[webmirror_tool]
)

backup_task = Task(
    description=f'Clone https://docs.company.com to ./backups/{datetime.now().strftime("%Y-%m-%d")}',
    agent=backup_agent
)

# Schedule with cron or similar
```

---

### 2. Competitive Intelligence

**Scenario:** Monitor competitor websites for changes

**Implementation:**
```python
competitors = [
    "https://competitor1.com",
    "https://competitor2.com",
    "https://competitor3.com"
]

for competitor in competitors:
    result = mcp_client.call_tool("clone_website", {
        "url": competitor,
        "output_dir": f"./intel/{competitor.replace('https://', '')}",
        "max_pages": 50
    })
```

---

### 3. Research Data Collection

**Scenario:** Collect datasets from multiple sources

**Claude Conversation:**
```
User: I need to collect data from these 10 research websites

Claude: I'll clone all 10 websites for your research.
[Sequentially calls clone_website for each]

Result: Collected data from all 10 sites:
- Site 1: 45 pages, 12.3 MB
- Site 2: 67 pages, 18.7 MB
...
Total: 543 pages, 156.8 MB across 10 sites
```

---

## 🔌 API Reference

### MCP Server Methods

#### `list_tools()`
Returns list of available tools with schemas.

#### `call_tool(name: str, arguments: dict)`
Executes a tool with given arguments.

**Supported Tools:**
- `clone_website`
- `download_file`
- `save_authentication`
- `list_saved_sessions`
- `get_site_info`

---

## 📖 Additional Resources

- **MCP Specification**: https://modelcontextprotocol.io
- **Claude Desktop**: https://claude.ai/desktop
- **CrewAI Docs**: https://docs.crewai.com
- **LangChain Tools**: https://python.langchain.com/docs/modules/agents/tools/
- **WebMirror CLI Guide**: `docs/CLI_GUIDE.md`
- **WebMirror GUI Guide**: `docs/GUI_GUIDE.md`

---

## 🤝 Contributing

WebMirror MCP server is open source! Contributions welcome:

1. **Report Issues**: https://github.com/ruslanmv/webmirror/issues
2. **Submit PRs**: Improvements to tools, documentation, examples
3. **Share Use Cases**: How are you using WebMirror MCP?

---

## 📄 License

Apache 2.0 - See LICENSE file

---

**Author**: Ruslan Magana
**Website**: [ruslanmv.com](https://ruslanmv.com)
**Version**: 1.0.0

---

*Making website cloning accessible to AI agents everywhere! 🤖*
