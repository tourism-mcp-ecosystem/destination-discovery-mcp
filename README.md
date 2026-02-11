# 🌍 Destination Discovery MCP

**An Intelligent Travel Oracle powered by Model Context Protocol**

---

## 🚀 The Vision

Traditional travel search is rigid. You shouldn't have to search for "Kyoto" or "Beaches"; you should be able to tell your AI Agent:

> *"Find me a place that feels historic but not touristy, with cool weather and a mid-range budget, perfect for solo photography."*

**Destination Discovery MCP** bridges the gap between natural language and structured destination data. It provides a multi-lingual tagging system that allows AI Agents to "think" like professional travel consultants.

---

## ✨ Key Features

* **🧠 Semantic Tagging Engine**: Uses a multi-lingual Trie structure (English, Chinese, Japanese) to understand *intent* rather than just keyword matching.
* **⚖️ Dynamic Weighted Matching**: Destinations are ranked by relevance scores (0.0 - 1.0), enabling nuanced "vibe-based" recommendations.
* **🔌 Native MCP Support**: Works out-of-the-box with **GitHub Copilot**, **Cursor**, and **Claude Desktop**.
* **🌱 Agentic Memory (Roadmap)**: Moving toward self-evolving knowledge where Agents can crawl the web to auto-update the destination database.

---

## 🛠️ Technical Architecture

| Component | Responsibility |
| --- | --- |
| **`mcp_server.py`** | Protocol layer (FastMCP). Registers tools for AI interaction. |
| **`label_manager.py`** | The brain. Handles Trie-based prefix searching and tag logic. |
| **`test_tags.json`** | Initial knowledge base (Categories, Synonyms, Weights). |

---

## 📥 Getting Started

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-username/destination-discovery-mcp.git
cd destination-discovery-mcp

# Install dependencies
pip install -r requirements.txt

```

### 2. Configure Your AI Client

Add this configuration to your MCP settings file (e.g., `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "travel-brain": {
      "command": "python",
      "args": ["D:/project/github/destination-discovery-mcp/main.py"],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}

```

---

## 🗺️ Project Roadmap

* [ ] **SQLite Migration**: Transition from JSON to a robust database for persistent memory.
* [ ] **Autonomous Learning**: Tool for Agents to crawl the web and auto-generate tags.
* [ ] **Vector Search**: Integrating embeddings for deep semantic understanding.

---

## 🤝 Contributing

We welcome global contributors!

* **Data Pathfinders**: Help us expand `test_tags.json` with more global destinations.
* **Architects**: Help us build the **SQLite-based Memory Set**.
* **Creative Engineers**: Improve the tagging algorithm to identify "vibe-based" descriptors like *"Cyberpunk"* or *"Quiet Luxury"*.

---

**Built with ❤️ for the Future of AI-assisted Travel**

---
