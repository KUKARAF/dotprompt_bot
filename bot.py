#!/usr/bin/env python3
"""
DotPrompt Bot - Telegram bot with LLM-first routing architecture

This bot always hits an LLM first to decide what to do, then executes the appropriate
prompts and tools. All LLM functions are defined in .runprompt/ directory.
"""

import os
import json
import yaml
import re
import importlib.util
from pathlib import Path
from telegram.ext import ApplicationBuilder, MessageHandler, filters
from telegram import Update
from dotenv import load_dotenv



load_dotenv()

class PromptBot:
    def __init__(self):
        self.prompts = {}  # prompt_name -> prompt_config
        self.tools = {}    # tool_name -> tool_function
        self.main_prompt = None  # Special main routing prompt
        
    def load_prompts(self):
        """Scan and load all .prompt files"""
        prompts_dir = Path("prompts")
        if not prompts_dir.exists():
            prompts_dir.mkdir(parents=True)
            return
            
        for prompt_file in prompts_dir.glob("*.prompt"):
            try:
                prompt_data = self._parse_prompt(prompt_file)
                prompt_name = prompt_file.stem
                self.prompts[prompt_name] = prompt_data
                print(f"✅ Loaded prompt: {prompt_name}")
                
                # Check if this is the main prompt
                if prompt_name == "main":
                    self.main_prompt = prompt_data
                    print(f"🎯 Set {prompt_name} as main routing prompt")
                
                # Load associated tools
                if "tools" in prompt_data.get("config", {}):
                    for tool_name in prompt_data["config"]["tools"]:
                        self._load_tool(tool_name)
                        
            except Exception as e:
                print(f"❌ Failed to load {prompt_file.stem}: {e}")
                continue
    
    def _parse_prompt(self, file_path):
        """Parse .prompt file into config + template"""
        with open(file_path) as f:
            content = f.read()
        
        parts = content.split("---")
        if len(parts) < 3:
            raise ValueError("Invalid prompt format")
            
        config = yaml.safe_load(parts[1])
        template = parts[2].strip()
        
        return {"config": config, "template": template}
    
    def _load_tool(self, tool_name):
        """Dynamically import and register tool"""
        if tool_name in self.tools:
            return
        
        tool_path = Path(f"tools/{tool_name}.py")
        if not tool_path.exists():
            raise FileNotFoundError(f"Tool not found: {tool_name}")
        
        spec = importlib.util.spec_from_file_location(tool_name, tool_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        self.tools[tool_name] = {
            "execute": module.execute,
            "metadata": module.TOOL_METADATA
        }
        
        print(f"✅ Loaded tool: {tool_name}")
    
    def _get_groq_client(self):
        """Get Groq client from local groq_client.py"""
        # Import groq_client locally to avoid circular imports
        import groq_client
        return groq_client.get_groq_client()
    
    def _call_llm_router(self, user_message: str, selected_prompts: list = None) -> dict:
        """Call the main LLM router to decide what action to take"""
        if not self.main_prompt:
            raise ValueError("Main routing prompt not found")
        
        client = self._get_groq_client()
        
        # Get available tools for context
        available_tools = list(self.tools.keys())
        available_prompts = list(self.prompts.keys())
        
        # Create system prompt with context
        system_prompt = self.main_prompt["config"].get("system_role", "You are a helpful assistant.")
        
        # Add available tools to system prompt
        tools_info = "\n".join([f"- {tool}: {self.tools[tool]['metadata']['description']}" 
                               for tool in available_tools])
        
        # Add selected prompts if provided
        selected_prompts_text = ", ".join(selected_prompts) if selected_prompts else "None"
        
        enhanced_system = f"""{system_prompt}

Available tools:
{tools_info}

Available prompts:
- {", ".join(available_prompts)}

Selected prompts from tool selector: {selected_prompts_text}

Current user message: ""{user_message}""

Analyze the message and respond with JSON indicating what action to take."""
        
        try:
            response = client.chat.completions.create(
                model=self.main_prompt["config"].get("model", "llama-3.1-70b"),
                messages=[
                    {"role": "system", "content": enhanced_system},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=self.main_prompt["config"].get("temperature", 0.1),
                max_tokens=self.main_prompt["config"].get("max_tokens", 2048)
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            print(f"❌ LLM router error: {e}")
            return {"action": "error", "error": str(e)}
    
    def render_template(self, template: str, variables: dict) -> str:
        """Simple template rendering with support for variables, if conditions, and each loops"""
        result = template
        
        # First, handle variable substitution
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        
        # Handle each loops first (they can affect if conditions)
        each_pattern = r'\{\{#each (\w+)\}\}(.*?)\{\{/each\}\}'
        for match in re.finditer(each_pattern, result, re.DOTALL):
            var_name = match.group(1)
            loop_content = match.group(2)
            
            if var_name in variables and isinstance(variables[var_name], list) and variables[var_name]:
                # Process each item in the list
                items_output = []
                for item in variables[var_name]:
                    # Create a copy of loop content for this item
                    item_content = loop_content
                    
                    # Replace {{this.property}} with item properties
                    this_pattern = r'\{\{this\.(\w+)\}\}'
                    for this_match in re.finditer(this_pattern, item_content):
                        prop_name = this_match.group(1)
                        if prop_name in item:
                            item_content = item_content.replace(this_match.group(0), str(item[prop_name]))
                        else:
                            item_content = item_content.replace(this_match.group(0), "")
                    
                    items_output.append(item_content)
                
                result = result.replace(match.group(0), "".join(items_output))
            else:
                # No items or not a list, remove the loop
                result = result.replace(match.group(0), "")
        
        # Handle if conditions after each loops
        if_pattern = r'\{\{#if (\w+)\}\}(.*?)(?:\{\{else\}\}(.*?))?\{\{/if\}\}'
        for match in re.finditer(if_pattern, result, re.DOTALL):
            var_name = match.group(1)
            if_content = match.group(2)
            else_content = match.group(3) if match.group(3) else ""
            
            if var_name in variables and variables[var_name]:
                result = result.replace(match.group(0), if_content)
            else:
                result = result.replace(match.group(0), else_content)
        
        return result
    
    async def execute_tool(self, tool_name: str, params: dict) -> dict:
        """Execute tool with error handling"""
        try:
            tool = self.tools[tool_name]
            result = tool["execute"](**params)
            return {"success": True, "data": result}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    async def execute_prompt(self, prompt_name: str, variables: dict) -> str:
        """Execute a specific prompt with given variables"""
        if prompt_name not in self.prompts:
            return f"❌ Prompt '{prompt_name}' not found"
        
        prompt_data = self.prompts[prompt_name]
        template = prompt_data["template"]
        rendered = self.render_template(template, variables)
        
        # If this prompt has tools, execute them first
        if "tools" in prompt_data["config"]:
            for tool_name in prompt_data["config"]["tools"]:
                tool_result = await self.execute_tool(tool_name, variables)
                if tool_result["success"]:
                    variables.update(tool_result["data"])
                else:
                    return f"❌ Tool error: {tool_result['error']}"
        
        return rendered
    
    def _call_tool_selector(self, user_message: str) -> dict:
        """Call the tool selector to determine which prompts to use"""
        if "tool_select" not in self.prompts:
            return {"selected_prompts": [], "reason": "Tool selector not available"}
        
        client = self._get_groq_client()
        
        # Get available prompts (excluding tool_select and main)
        available_prompts = [p for p in self.prompts.keys() if p not in ["tool_select", "main"]]
        
        # Create system prompt with context
        system_prompt = self.prompts["tool_select"]["config"].get("system_role", "You are a prompt selector.")
        
        # Add available prompts to system prompt
        prompts_info = "\n".join([f"- {prompt}: {self.prompts[prompt]['config'].get('description', 'No description')}" 
                               for prompt in available_prompts])
        
        enhanced_system = f"""{system_prompt}

Available prompts:
{prompts_info}

Current user message: "{user_message}"

Analyze the message and respond with JSON indicating which prompts should be used."""
        
        try:
            response = client.chat.completions.create(
                model=self.prompts["tool_select"]["config"].get("model", "llama-3.1-70b"),
                messages=[
                    {"role": "system", "content": enhanced_system},
                    {"role": "user", "content": user_message}
                ],
                response_format={"type": "json_object"},
                temperature=self.prompts["tool_select"]["config"].get("temperature", 0.1),
                max_tokens=self.prompts["tool_select"]["config"].get("max_tokens", 1024)
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
            
        except Exception as e:
            print(f"❌ Tool selector error: {e}")
            return {"selected_prompts": [], "reason": f"Error: {str(e)}"}
    
    async def handle_message(self, update: Update, context):
        """Handle incoming Telegram message - always hit tool selector first, then LLM router"""
        user_message = update.message.text
        print(f"📥 Received message: {user_message}")
        
        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )
        
        try:
            # Step 1: Call tool selector to determine which prompts to use
            tool_selection = self._call_tool_selector(user_message)
            selected_prompts = tool_selection.get("selected_prompts", [])
            print(f"🔧 Tool selector decision: {tool_selection}")
            
            # Step 2: Always hit LLM router first to decide what to do
            routing_decision = self._call_llm_router(user_message, selected_prompts)
            print(f"🤖 LLM routing decision: {routing_decision}")
            
            action = routing_decision.get("action")
            parameters = routing_decision.get("parameters", {})
            
            # Step 2: Execute the decided action
            if action == "search_obsidian":
                # Execute obsidian search
                result = await self.execute_tool("search_obsidian", parameters)
                if result["success"]:
                    # Render the obsidian prompt template with the tool results
                    # We don't call execute_prompt because that would re-execute the tool
                    # Instead, we directly render the template with the results we already have
                    response = self.render_template(
                        self.prompts["obsidian"]["template"], 
                        {
                            "query": parameters.get("query", user_message), 
                            "results": result["data"]["results"]
                        }
                    )
                else:
                    response = f"❌ Search error: {result['error']}"
                    
            elif action == "help":
                # Provide help
                help_text = "🤖 **DotPrompt Bot**\n\n"
                help_text += "Available commands:\n"
                help_text += "• Search notes: 'search notes about X'\n"
                help_text += "• Find in Obsidian: 'find in obsidian Y'\n"
                help_text += "• General questions: Just ask!\n"
                response = help_text
                
            elif action == "error":
                response = f"❌ Error: {routing_decision.get('error', 'Unknown error')}"
                
            else:
                # Unknown action, provide generic help
                response = "🤔 I'm not sure how to handle that request. Try asking about something specific!"
                
            await update.message.reply_text(response)
            
        except Exception as e:
            print(f"❌ Error handling message: {e}")
            await update.message.reply_text(f"❌ Sorry, I encountered an error: {str(e)}")

def main():
    print("🚀 Starting DotPrompt Bot with LLM-first routing...")
    bot = PromptBot()
    bot.load_prompts()
    
    if not bot.main_prompt:
        print("❌ Main routing prompt not found! Please create .runprompt/prompts/main.prompt")
        return
    
    token = os.getenv("TELEGRAM_TOKEN")
    if not token or token == "your_bot_token_here":
        print("❌ Please set TELEGRAM_TOKEN in .env file")
        return
    
    app = ApplicationBuilder().token(token).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("🎉 Bot is running! All messages will be routed through LLM first.")
    app.run_polling()

if __name__ == "__main__":
    main()