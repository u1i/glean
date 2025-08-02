#!/Users/uli/projects/glean/venv/bin/python
"""
Glean - A command-line tool for analyzing text using OpenRouter API with language models.
Sister project to Glimpse for images.
"""

import argparse
import configparser
import json
import os
import sys
import requests
from pathlib import Path


class GleanConfig:
    """Handle configuration loading and validation."""
    
    def __init__(self):
        self.config_path = Path.home() / '.glean_cfg'
        self.api_key = None
        self.model = 'google/gemini-2.0-flash-exp'  # Default model
        self.temperature = 0.4  # Default temperature
        self.system_prompt = None  # Optional system prompt
        
    def load_config(self):
        """Load configuration from ~/.glean_cfg file."""
        if not self.config_path.exists():
            print(f"Error: Configuration file not found at {self.config_path}")
            print("Please create ~/.glean_cfg with your OpenRouter API key.")
            print("See README.md for configuration format.")
            sys.exit(1)
            
        config = configparser.ConfigParser()
        try:
            config.read(self.config_path)
            
            if 'openrouter' not in config:
                print("Error: [openrouter] section not found in config file.")
                sys.exit(1)
                
            openrouter_section = config['openrouter']
            
            # Required setting
            if 'api_key' not in openrouter_section:
                print("Error: api_key not found in [openrouter] section.")
                sys.exit(1)
            self.api_key = openrouter_section['api_key']
            
            # Optional settings with defaults
            if 'model' in openrouter_section:
                self.model = openrouter_section['model']
            if 'temperature' in openrouter_section:
                try:
                    self.temperature = float(openrouter_section['temperature'])
                except ValueError:
                    print("Warning: Invalid temperature value in config. Using default 0.4")
            if 'system_prompt' in openrouter_section:
                self.system_prompt = openrouter_section['system_prompt']
                    
        except Exception as e:
            print(f"Error reading configuration file: {e}")
            sys.exit(1)


class GleanAnalyzer:
    """Main analyzer class for processing text with OpenRouter API."""
    
    def __init__(self, config):
        self.config = config
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        
    def get_default_prompt(self):
        """Return the default analysis prompt."""
        return """Please provide a comprehensive analysis of the following text including:
1. A concise summary
2. Key points and main themes
3. Important insights or takeaways
4. Any notable patterns or structure

Please be thorough but concise in your analysis."""

    def analyze_text(self, text, custom_prompt=None, model_override=None, temperature_override=None):
        """Analyze text using OpenRouter API."""
        if not text.strip() and not custom_prompt:
            print("Error: No text provided for analysis.")
            return None
            
        # Use overrides if provided, otherwise use config values
        model = model_override if model_override else self.config.model
        temperature = temperature_override if temperature_override is not None else self.config.temperature
        
        # Prepare the prompt
        if custom_prompt:
            if text.strip():
                prompt = f"{custom_prompt}\n\nText to analyze:\n{text}"
            else:
                prompt = custom_prompt
        else:
            prompt = f"{self.get_default_prompt()}\n\nText to analyze:\n{text}"
            
        # Prepare API request
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        # Prepare messages array
        messages = []
        if self.config.system_prompt:
            messages.append({
                "role": "system",
                "content": self.config.system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        data = {
            "model": model,
            "messages": messages,
            "temperature": temperature
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                print("Error: Unexpected API response format.")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"Error making API request: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing API response: {e}")
            return None


def read_text_file(filepath):
    """Read text from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}")
        sys.exit(1)


def read_stdin():
    """Read text from stdin."""
    try:
        return sys.stdin.read()
    except Exception as e:
        print(f"Error reading from stdin: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze text using OpenRouter API with language models.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.txt
  %(prog)s notes.md --prompt "Summarize the key points"
  echo "Analyze this text" | %(prog)s
  %(prog)s report.txt -m openai/gpt-4o-mini -t 0.2
        """
    )
    
    parser.add_argument('file', nargs='?', help='Text file to analyze (if not provided, reads from stdin)')
    parser.add_argument('-p', '--prompt', help='Custom prompt for analysis')
    parser.add_argument('-m', '--model', help='Override the model specified in config')
    parser.add_argument('-t', '--temperature', type=float, help='Override the temperature setting (0.0-1.0)')
    
    args = parser.parse_args()
    
    # Validate temperature if provided
    if args.temperature is not None and (args.temperature < 0.0 or args.temperature > 1.0):
        print("Error: Temperature must be between 0.0 and 1.0")
        sys.exit(1)
    
    # Load configuration
    config = GleanConfig()
    config.load_config()
    
    # Get text input
    if args.file:
        # Check if file has supported extension
        file_path = Path(args.file)
        if file_path.suffix.lower() not in ['.txt', '.md', '']:
            print(f"Warning: File extension '{file_path.suffix}' may not be optimal for text analysis.")
        text = read_text_file(args.file)
    else:
        # Read from stdin
        if sys.stdin.isatty():
            print("Error: No file provided and no input from stdin.")
            print("Usage: glean.py <file> or echo 'text' | glean.py")
            sys.exit(1)
        text = read_stdin()
    
    # Initialize analyzer and process text
    analyzer = GleanAnalyzer(config)
    result = analyzer.analyze_text(
        text, 
        custom_prompt=args.prompt,
        model_override=args.model,
        temperature_override=args.temperature
    )
    
    if result:
        print(result)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
