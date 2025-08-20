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
import time
import tempfile
import requests
import urllib3
from pathlib import Path

# Suppress SSL warnings when verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class GleanConfig:
    """Handle configuration loading and validation."""
    
    def __init__(self):
        self.config_path = Path.home() / '.glean_cfg'
        self.api_key = None
        self.model = 'google/gemini-2.0-flash-exp'  # Default model
        self.temperature = 0.4  # Default temperature
        self.system_prompt = None  # Optional system prompt
        self.http_proxy = None  # Optional HTTP proxy
        
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
            if 'http_proxy' in openrouter_section:
                self.http_proxy = openrouter_section['http_proxy']
                    
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
            "Content-Type": "application/json",
            "X-Title": "glean",
            "HTTP-Referer": "https://github.com/u1i/glean"
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
        
        # Prepare proxy settings if configured
        proxies = {}
        if self.config.http_proxy:
            proxies = {
                'http': self.config.http_proxy,
                'https': self.config.http_proxy
            }
        
        try:
            response = requests.post(self.api_url, headers=headers, json=data, proxies=proxies, verify=False)
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


def get_cache_file_path():
    """Get the path for the models cache file."""
    return os.path.join(tempfile.gettempdir(), 'glean_models_cache.json')


def is_cache_valid(cache_file_path, max_age_hours=6):
    """Check if the cache file exists and is not older than max_age_hours."""
    if not os.path.exists(cache_file_path):
        return False
    
    file_age = time.time() - os.path.getmtime(cache_file_path)
    max_age_seconds = max_age_hours * 3600
    return file_age < max_age_seconds


def load_models_from_cache(cache_file_path):
    """Load models data from cache file."""
    try:
        with open(cache_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_models_to_cache(models_data, cache_file_path):
    """Save models data to cache file."""
    try:
        with open(cache_file_path, 'w', encoding='utf-8') as f:
            json.dump(models_data, f)
    except IOError:
        # If we can't write to cache, just continue without caching
        pass


def fetch_models_data():
    """Fetch models data from API or cache."""
    cache_file_path = get_cache_file_path()
    
    # Try to load from cache first
    if is_cache_valid(cache_file_path):
        cached_data = load_models_from_cache(cache_file_path)
        if cached_data is not None:
            return cached_data
    
    # Cache miss or invalid - fetch from API
    try:
        # Note: Model listing endpoint doesn't need proxy since it's public and doesn't require auth
        response = requests.get("https://openrouter.ai/api/v1/models")
        response.raise_for_status()
        
        models_data = response.json()
        
        # Save to cache
        save_models_to_cache(models_data, cache_file_path)
        
        return models_data
        
    except requests.exceptions.RequestException as e:
        # If API fails, try to load from cache even if expired
        cached_data = load_models_from_cache(cache_file_path)
        if cached_data is not None:
            print(f"Warning: API request failed, using cached data: {e}")
            return cached_data
        else:
            raise e


def list_models(detailed=True):
    """List all available OpenRouter models."""
    try:
        models_data = fetch_models_data()
        
        if 'data' in models_data:
            models = models_data['data']
        else:
            models = models_data  # Fallback if response format is different
        
        if detailed:
            print(f"Available OpenRouter Models ({len(models)} total):")
            print("=" * 60)
            
            for model in models:
                model_id = model.get('id', 'Unknown')
                name = model.get('name', 'Unknown')
                context_length = model.get('context_length', 'Unknown')
                
                # Get pricing info
                pricing = model.get('pricing', {})
                prompt_price = pricing.get('prompt', '0')
                completion_price = pricing.get('completion', '0')
                
                # Format pricing (convert to more readable format)
                try:
                    prompt_cost = f"${float(prompt_price) * 1000:.4f}/1K"
                    completion_cost = f"${float(completion_price) * 1000:.4f}/1K"
                except (ValueError, TypeError):
                    prompt_cost = "N/A"
                    completion_cost = "N/A"
                
                print(f"ID: {model_id}")
                print(f"Name: {name}")
                print(f"Context: {context_length} tokens")
                print(f"Pricing: {prompt_cost} prompt, {completion_cost} completion")
                
                # Add description if available and not too long
                description = model.get('description', '')
                if description and len(description) <= 100:
                    print(f"Description: {description}")
                elif description:
                    print(f"Description: {description[:97]}...")
                
                print("-" * 60)
        else:
            # Simple list of model IDs only
            print(f"Available OpenRouter Models ({len(models)} total):")
            for model in models:
                model_id = model.get('id', 'Unknown')
                print(model_id)
            
    except Exception as e:
        print(f"Error fetching models: {e}")
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
    parser.add_argument('--list-models', action='store_true', help='List all available OpenRouter model names')
    parser.add_argument('--list-models-with-details', action='store_true', help='List all available OpenRouter models with detailed information')
    
    args = parser.parse_args()
    
    # Handle --list-models commands
    if args.list_models:
        list_models(detailed=False)
        sys.exit(0)
    
    if args.list_models_with_details:
        list_models(detailed=True)
        sys.exit(0)
    
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
        # Check if we have stdin input or if we can run prompt-only
        if sys.stdin.isatty():
            # Interactive terminal - check if we have a custom prompt for prompt-only mode
            if args.prompt:
                text = ""  # Empty text, will use prompt-only mode
            else:
                print("Error: No file provided and no input from stdin.")
                print("Usage: glean.py <file> or echo 'text' | glean.py or glean.py -p 'prompt'")
                sys.exit(1)
        else:
            # Read from stdin (piped input)
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
