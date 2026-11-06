# 🎬 resolve-mcp-server

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)

**Connect AI agents to [DaVinci Resolve Studio](https://www.blackmagicdesign.com/products/davinciresolve/studio).**

`resolve-mcp-server` is a local [Model Context Protocol (MCP)](https://github.com/modelcontextprotocol) server built with the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) that wraps the [DaVinci Resolve Studio](https://www.blackmagicdesign.com/products/davinciresolve/studio) Python Scripting API. It allows MCP-compatible AI assistants to inspect your active project and timeline, read clip metadata, add markers, manage media pool folders, and automate post-production workflows using natural language.

## ✨ Features

- **Context-Aware Inspection:** Query the active project, list timelines, inspect track counts, and read clip properties and frame ranges across video, audio, and subtitle tracks.
- **Timeline Automation:** Create new timelines, switch active timelines, and add color-coded timeline markers with custom notes and durations at exact frame offsets.
- **Media Pool Management:** Inspect bins, list imported media clips, import new media files from disk, and create timelines directly from selected media pool clips.
- **Render Queue Control:** Load render presets, create render jobs, and trigger or check render status directly from your AI assistant.
- **Local & Secure:** Runs entirely on your machine over standard I/O (`stdio`), keeping your project data local unless queried by your client.

## 📋 Prerequisites

1. **[DaVinci Resolve Studio](https://www.blackmagicdesign.com/products/davinciresolve/studio) 18+** (The free edition of DaVinci Resolve does not support external Python API scripting).
2. **[Python 3.10+](https://www.python.org/downloads/)** with the [MCP Python SDK Documentation](https://py.sdk.modelcontextprotocol.io/).
3. **External Scripting Enabled** inside DaVinci Resolve Studio:
   - Open `DaVinci Resolve` > `Preferences` > `System` > `General`
   - Set **External scripting using** to **Local**
   - Restart DaVinci Resolve Studio and open a project.

## 🚀 Installation

1. Clone the repository from [GitHub](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository):
   ```bash
   git clone https://github.com/arham837/resolve-mcp-server.git
   cd resolve-mcp-server
   ```

2. Create a virtual environment and install the package:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -e ".[dev]"
   ```

3. (Optional) Override environment variables if DaVinci Resolve Studio is installed in a non-standard path:
   - **macOS (Default):**
     - `RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"`
     - `RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"`
   - **Windows (Default):**
     - `RESOLVE_SCRIPT_API="%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"`
     - `RESOLVE_SCRIPT_LIB="C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"`
   - **Linux (Default):**
     - `RESOLVE_SCRIPT_API="/opt/resolve/Developer/Scripting"`
     - `RESOLVE_SCRIPT_LIB="/opt/resolve/libs/Fusion/fusionscript.so"`

## ⚙️ MCP Client Configuration

Add `resolve-mcp-server` to your MCP client configuration file (for example, `claude_desktop_config.json` or your IDE's MCP settings):

```json
{
  "mcpServers": {
    "davinci-resolve": {
      "command": "/absolute/path/to/resolve-mcp-server/.venv/bin/resolve-mcp-server",
      "args": []
    }
  }
}
```

Or run the server directly during development:

```bash
python -m resolve_mcp_server
```

## 🛠️ Available MCP Tools

| Tool Name | Description |
| :--- | :--- |
| `get_project_info` | Returns the active DaVinci Resolve project name, frame rate, resolution, and timeline count. |
| `list_timelines` | Lists all timelines in the current project and indicates which timeline is active. |
| `set_current_timeline` | Switches the active timeline by name. |
| `get_timeline_details` | Returns track counts (video, audio, subtitle), start/end timecodes, and markers on the active timeline. |
| `list_timeline_clips` | Lists all clips on a specified track (`video`, `audio`, or `subtitle`) and track index, including start/end frames and clip names. |
| `add_timeline_marker` | Adds a color-coded marker (`Blue`, `Cyan`, `Green`, `Yellow`, `Red`, `Pink`, `Purple`, `Fuchsia`, `Rose`, `Lavender`, `Sky`, `Mint`, `Lemon`, `Sand`, `Cocoa`, `Cream`) at a specific frame offset with a name, note, and duration. |
| `delete_timeline_markers_by_color` | Removes markers of a specific color (or `All`) from the active timeline. |
| `list_media_pool_clips` | Lists all clips in the current Media Pool folder along with clip properties (resolution, FPS, duration). |
| `import_media` | Imports one or more local file paths into the active Media Pool bin. |
| `create_timeline_from_clips` | Creates a new timeline with the specified name from clips in the current Media Pool folder. |
| `start_render` | Adds a render job for the active timeline (optional preset name and target directory) and starts rendering. |

## 🧪 Running Tests

Unit tests use a mocked DaVinci Resolve API so you can test all MCP tools without launching DaVinci Resolve Studio:

```bash
python3 -m unittest discover -s tests
```

## 📂 Project Structure

```text
resolve-mcp-server/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── LICENSE
├── README.md
├── pyproject.toml
├── src/
│   └── resolve_mcp_server/
│       ├── __init__.py
│       ├── __main__.py
│       ├── resolve_client.py
│       └── server.py
└── tests/
    └── test_server.py
```

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/amazing-feature`)
3. Commit your Changes (`git commit -m 'Add amazing feature'`)
4. Push to the Branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

Distributed under the [MIT License](https://opensource.org/license/mit). See `LICENSE` for more information.
