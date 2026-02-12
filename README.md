# Telegram Bot with DotPrompt Architecture

A minimal Telegram bot that dynamically loads capabilities from `.prompt` files and their associated tools.

## Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment:
```bash
cp .env.example .env
# Edit .env with your tokens
```

3. Create directories:
```bash
mkdir -p .runprompt/prompts
mkdir -p .runprompt/tools
```

4. Run:
```bash
python bot.py
```

## Adding Capabilities

To add a new capability:

1. Create a tool in `.runprompt/tools/`
2. Create a prompt in `.runprompt/prompts/`
3. Restart the bot

No code changes needed!

## Example

The included `obsidian.prompt` lets users search their Obsidian vault by saying:
- "search notes about python"
- "find in obsidian"
- "obsidian"

## Architecture Flow

1. **Tool Selector** (`tool_select.prompt`): First analyzes the user message and selects appropriate prompt files (cannot select itself or main)
2. **Main Router** (`main.prompt`): Uses the selected prompts and available tools to decide what action to take
3. **Execution**: The bot executes the decided action using the appropriate tools and prompts

## Adding New Prompts

When adding new prompts, the tool selector will automatically consider them for selection based on the user's input.
