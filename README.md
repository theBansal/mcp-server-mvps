# Jenkins MCP Server

A lightweight MCP (Model Context Protocol) server to integrate and automate Jenkins operations, designed for seamless interaction with Claude Desktop.

---

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the MCP Server](#running-the-mcp-server)
- [Integrating with Claude Desktop](#integrating-with-claude-desktop)
- [Usage](#usage)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Overview

This project provides an MCP (Model Context Protocol) server that acts as a bridge between Jenkins and Claude Desktop, enabling you to trigger builds, read logs, monitor jobs, and more via natural language commands.

---

## Prerequisites

- [Docker](https://www.docker.com/) (for running Jenkins locally)
- [Python 3.8+](https://www.python.org/)
- [`uv`](https://github.com/astral-sh/uv) (a fast Python package installer and runner)
- Jenkins API token and user credentials

---

## Installation

### 1. Set Up Jenkins (Local Demo)

You can quickly spin up a local Jenkins server using Docker:

```sh
docker run -p 8080:8080 -p 50000:50000 jenkins/jenkins:lts
```

- Access Jenkins at [http://localhost:8080](http://localhost:8080)
- Create a user and generate an API token for that user (Manage Jenkins → Manage Users → Your User → Configure → API Token)

### 2. Install `uv`

[`uv`](https://github.com/astral-sh/uv) is a fast Python package manager and runner, serving as a drop-in replacement for pip and venv. It ensures reproducible, isolated environments.

**Install `uv`:**

```sh
curl -Ls https://astral.sh/uv/install.sh | sh
```

Or, if you have pipx:

```sh
pipx install uv
```

### 3. Install Project Dependencies

Inside the project directory, run:

```sh
uv pip install -r requirements.txt
```

This will create a virtual environment and install all required dependencies.

---

## Running the MCP Server

1. **Set Environment Variables**

   - Copy `.env.example` to `.env` and fill in your Jenkins server details and credentials, or set them manually in your shell.

2. **Start the Server**

   ```sh
   uv run jenkins-mcp-server.py
   ```

   Keep this server running to allow communication with Claude Desktop.

---

## Integrating with Claude Desktop

1. **Install Claude Desktop** (from [here](https://www.anthropic.com/claude/desktop) or your preferred source)
2. Open **Settings → Developer → MCP Server → Edit Config**
3. Replace the `clause_desktop_config.json` file with the one provided in this repo, or merge its contents into your existing config.
   - Ensure the path to `jenkins-mcp-server.py` is correct in the config.
4. **Restart Claude Desktop** to apply changes.

---

## Usage

Once setup is complete, you can interact with Claude Desktop to:

- Trigger Jenkins builds
- Read build logs
- Monitor job statuses
- And much more, all via natural language

---

## Troubleshooting

- **Connectivity Issues:**  
  If Claude Desktop cannot connect to Jenkins via the MCP server, check the MCP server logs for errors.

- **Missing Packages:**  
  If you see errors about missing packages, install them in the environment where Claude Desktop is running.

  ```sh
  uv pip install <missing-package>
  ```

- **Jenkins API Issues:**  
  Ensure your Jenkins user has the correct permissions and the API token is valid.

---

## FAQ

**Q: What is `uv` and why use it?**  
A: `uv` is a fast, modern Python package manager and runner. It creates isolated environments and installs dependencies much faster than pip, making setup and reproducibility easier.

**Q: Can I use pip/venv instead of uv?**  
A: Yes, but `uv` is recommended for speed and simplicity. If you prefer pip, use `python -m venv venv` and `pip install -r requirements.txt`.

---

For further questions or issues, please open an issue in this repository.

