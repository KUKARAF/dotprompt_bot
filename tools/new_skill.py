#!/usr/bin/env python3
"""
New Skill Tool - Create new runprompt prompts and tools
"""

import os
import requests

def get_runprompt_docs():
    """
    Fetch the runprompt README documentation from GitHub.
    
    Returns:
        The runprompt README.md content
    """
    try:
        url = "https://raw.githubusercontent.com/chr15m/runprompt/refs/heads/main/README.md"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        return f"Error fetching documentation: {str(e)}"

get_runprompt_docs.safe = True


def create_prompt(filename: str, content: str):
    """
    Create a new .prompt file in ~/.config/dotfiles/.runprompt/prompts/
    
    Args:
        filename: Name of the prompt file (should end with .prompt)
        content: The complete content of the prompt file
        
    Returns:
        Success message or error
    """
    try:
        # Ensure filename ends with .prompt
        if not filename.endswith('.prompt'):
            filename += '.prompt'
        
        # Hardcoded path
        prompts_dir = os.path.expanduser('~/.config/dotfiles/.runprompt/prompts')
        os.makedirs(prompts_dir, exist_ok=True)
        
        filepath = os.path.join(prompts_dir, filename)
        
        # Write file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return f"Successfully created {filepath}"
    except Exception as e:
        return f"Error creating prompt: {str(e)}"

# Not marked as safe - creates files


def create_tool(filename: str, content: str):
    """
    Create a new .py tool file in ~/.config/dotfiles/.runprompt/tools/
    
    Args:
        filename: Name of the tool file (should end with .py)
        content: The complete Python code for the tool
        
    Returns:
        Success message or error
    """
    try:
        # Ensure filename ends with .py
        if not filename.endswith('.py'):
            filename += '.py'
        
        # Hardcoded path
        tools_dir = os.path.expanduser('~/.config/dotfiles/.runprompt/tools')
        os.makedirs(tools_dir, exist_ok=True)
        
        filepath = os.path.join(tools_dir, filename)
        
        # Write file
        with open(filepath, 'w') as f:
            f.write(content)
        
        return f"Successfully created {filepath}"
    except Exception as e:
        return f"Error creating tool: {str(e)}"

# Not marked as safe - creates files
