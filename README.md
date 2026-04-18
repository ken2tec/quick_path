<p align="center">
  <img src="assets/logo.png" alt="Quick Path Logo" width="200"/>
</p>

# 🚀 Quick Path

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

**Quick Path** is a lightweight, high-speed CLI tool designed for developers and power users who navigate through dozens of project directories and documentation folders daily. Say goodbye to deep directory nesting and fragmented shortcuts.

---

## ✨ Key Features

- **📂 Path Management**: Organize your workspace, documentation, and project paths in a simple `.ini` file.
- **⚡ Rapid Navigation**: Instantly open folders in File Explorer or Windows Terminal with a single keystroke.
- **Smart Clipboard**: Copy paths or capture command output directly to your clipboard.
- **📜 Command History**: Sync command results are automatically logged to SQLite for easy retrieval later.
- **🛠️ Custom Actions**: Define your own shortcuts to launch applications (e.g., VS Code, Antigravity) or run CLI commands.
- **🌗 TUI (Text User Interface)**: A clean, keyboard-driven interface that feels fast and responsive.

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/quick_path.git
   cd quick_path
   ```

2. **Run from source**:
   - Install dependencies (if any, standard Python library used):
     ```bash
     python main.py
     ```
   - *Note: Requires `msvcrt` (Windows only).*

3. **Build the executable**:
   We provide a PowerShell script for building a standalone `.exe` using PyInstaller.
   ```powershell
   .\build.ps1
   ```

## 🚀 Getting Started

Launch the application using the executable or `main.py`. The tool will automatically load `main.ini`.

### Controls

| Key | Action |
| :--- | :--- |
| **Arrow Up/Down** | Highlight a path or directory |
| **Enter** | Enter directory / Open file in Explorer |
| **[ .. ]** | Go back to parent / Main menu |
| **[e]** | **Explore**: Open selected path in File Explorer |
| **[t]** | **Terminal**: Open selected path in Windows Terminal |
| **[c]** | **Copy**: Copy path to clipboard |
| **[h]** | **History**: View, re-copy [c], export [f], or delete [d] past sync command outputs |
| **[q]** | **Quit**: Exit the application |
| **Custom Keys** | Executed defined sync/async commands |

## ⚙️ Configuration (`main.ini`)

Customize your paths and shortcuts in the configuration file.

```ini
[Paths]
Projects = D:\Dev\Projects
Docs = C:\Users\User\Documents

[Commands]
v = VSCODE, code {path}
a = Antigravity, antigravity {path}

[SyncCommands]
g = GitStatus, git status
```

- **[Commands]**: Launch apps asynchronously (background).
- **[SyncCommands]**: Run commands and capture output to the clipboard.
- **{{Parameter}} Support**: Use `{{name}}` placeholders to prompt for user input before command execution.

### 📋 Command Reference (Standard Definition)

The following commands are pre-defined in `main.ini` for quick access and common tasks.

#### `[Commands]` (Async / Background)
| Key | Label | Description |
| :--- | :--- | :--- |
| **v** | **VSCODE** | Open selected path in Visual Studio Code. |
| **a** | **Antigravity** | Open selected path in Antigravity. |
| **b** | **GitBash** | Launch Git Bash in the selected directory. |
| **m** | **Memorandum** | Open a simple GUI scratchpad for quick notes. |
| **p** | **ProcessToCsv** | Dump detailed process list to a CSV file. |
| **w** | **WatchFolder** | Monitor file changes in a specific directory. |
| **x** | **XlsxToCsv** | Convert selected Excel sheet to CSV. |
| **y** | **WatchClipboard** | Monitor and log clipboard changes in a GUI window. |

#### `[SyncCommands]` (Sync / Logged to Clipboard)
| Key | Label | Description |
| :--- | :--- | :--- |
| **d** | **Du** | Display directory usage (Customizable depth). |
| **u** | **DuFull** | Recursive disk usage calculation exported to CSV. |
| **r** | **Tree** | View directory structure with file sizes and timestamps. |
| **f** | **Find** | Search files by name using RegExp. |
| **g** | **Grep** | Search text content within files. |
| **j** | **FindWith7z** | Search files inside archives (zip, 7z, etc.). |
| **k** | **GrepWith7z** | Full-text search inside archived files. |
| **l** | **ScoopList** | List installed Scoop packages and binaries. |
| **s** | **PingSweep** | Perform a network ping sweep on a range. |
| **i** | **GitStatus** | Execute `git status` and capture output. |

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<p align="center">Made with ❤️ for efficiency by your-name</p>
