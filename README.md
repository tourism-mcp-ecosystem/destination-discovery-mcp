🌍 Destination Discovery MCP: The AI Travel Oracle
Transforming vague travel dreams into structured destination insights through the Model Context Protocol.

🚀 The Vision
Traditional travel search is broken. You shouldn't have to search for "Kyoto" or "Beaches"; you should be able to tell your AI:

"Find me a place that feels historic but not touristy, with cool weather and a mid-range budget, perfect for solo photography."

Destination Discovery MCP bridges the gap between human language and destination data. It provides a structured, multi-lingual tagging system that allows AI Agents to "think" like travel experts.

✨ Key Features
🧠 Semantic Tagging Engine: Uses a multi-lingual Trie structure to manage synonyms across English, Chinese, Japanese, and more. It doesn't just match keywords; it understands intent.

⚖️ Dynamic Weighted Matching: Destinations aren't just lists; they are weighted datasets. Each tag has a relevance score (0.0 - 1.0), allowing for nuanced rankings based on specific user vibes.

🔌 Zero-Config Integration: Fully compatible with GitHub Copilot, Cursor, and Claude Desktop. One line of config gives your AI a professional travel guidebook's worth of knowledge.

🌱 Self-Evolving Knowledge (Experimental): Our roadmap includes "Agentic Memory," where the server crawls travelogues and uses LLMs to extract and save new tags and destinations automatically.

🛠️ Technical Architecture
This project is built for scalability and performance:

Core Logic (label_manager.py): Handles the complex Trie-based prefix searching and multi-lingual MultilingualTag data classes.

MCP Interface (mcp_server.py): A FastMCP-powered server that registers tools for tag search, destination matching, and database management.

Data Layer: Currently using optimized JSON for portability, with a migration to SQLite planned for persistent "Agent Memory."

📥 Quick Start
1. Clone & Setup
Bash
git clone https://github.com/your-username/destination-discovery-mcp.git
cd destination-discovery-mcp
pip install -r requirements.txt
2. Configure your AI Client
Add this to your .vscode/mcp.json or Copilot settings:

JSON
{
  "mcpServers": {
    "travel-brain": {
      "command": "python",
      "args": ["D:/path/to/your/project/main.py"],
      "env": { "PYTHONUTF8": "1" }
    }
  }
}
🤝 Join the Expedition!
We are looking for travelers and coders who want to build the future of AI exploration.

Data Pathfinders: Help us expand test_tags.json to cover more global hidden gems.

Architects: Help us transition from JSON to a robust SQLite-based Memory Set.

Creative Engineers: Design tools that can extract "vibe-based" tags (like "Cyberpunk-ish" or "Wes Anderson style") from raw text.

Star ⭐ this repo to help more people discover their next adventure!

What's next on our itinerary?
Would you like me to start on Task A (The SQLite Migration) to give your server permanent memory, or Task B (The Auto-Discovery Tool) so your Agent can start learning about new cities from the web?