# Glean

A command-line tool for analyzing text using OpenRouter API with language models. Sister project to [Glimpse](https://github.com/u1i/glimpse) for images.

## Installation

1. Clone this repository
2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. The script is now ready to use! It's directly executable without needing to specify the Python interpreter.

## Configuration

Create a `~/.glean_cfg` file in your home directory with the following format:

```ini
[openrouter]
# Required setting
api_key = your_api_key_here

# Optional settings (defaults shown)
model = google/gemini-2.0-flash-exp
temperature = 0.4  # Controls randomness (0.0 to 1.0, lower is more deterministic)
system_prompt = You are a helpful assistant.  # Optional system prompt for all requests
http_proxy = http://localhost:8888  # Optional HTTP proxy for API requests
```

Only the API key is mandatory. If model, temperature, system_prompt, or http_proxy are not specified, default values will be used (no system prompt or proxy by default).

## Project Structure

```
glean/
├── glean.py          # Main executable script
├── requirements.txt  # Python dependencies
├── venv/            # Virtual environment (created during setup)
├── .gitignore       # Git ignore file
└── README.md        # This file
```

## Usage

From a file:
```bash
./glean.py document.txt
./glean.py notes.md
```

From stdin:
```bash
echo "Analyze this text" | ./glean.py
cat article.txt | ./glean.py
```

With a custom prompt:
```bash
./glean.py document.txt --prompt "Summarize the key points"
cat article.md | ./glean.py -p "Extract all action items"
```

Override the model:
```bash
./glean.py notes.txt --model anthropic/claude-3.5-haiku
```

Override the temperature setting:
```bash
./glean.py document.md --temperature 0.8
```

Combining options:
```bash
./glean.py report.txt -m openai/gpt-4o-mini -t 0.2 -p "What are the main risks mentioned?"
```

List available models (names only):
```bash
./glean.py --list-models
```

List available models with detailed information:
```bash
./glean.py --list-models-with-details
```

## Shell Script Usage

When using Glean in shell scripts, be aware that it captures stdin. For processing multiple prompts or files, you need to redirect stdin appropriately:

```bash
#!/bin/bash

# Single prompt in a script
./glean.py -p "Analyze this data" < /dev/null

# Process multiple prompts from a file (handles prompts with spaces)
while read -r p; do 
    ./glean.py -p "$p" < /dev/null
done < prompts.txt

# Process multiple files with the same prompt
for file in *.txt; do
    ./glean.py "$file" -p "Summarize this document" < /dev/null
done

# Combine with other commands (redirect stdin to avoid conflicts)
echo "Processing files..." | while read -r line; do
    ./glean.py -p "What is the main topic?" < /dev/null
done
```

**Important:** Always use `< /dev/null` when calling Glean in loops or scripts to prevent it from consuming stdin that should be used by the loop itself.

## Supported Text Formats

- Plain text (.txt)
- Markdown (.md)
- Text from stdin

## Default Behavior

Without a custom prompt, Glean will provide a comprehensive analysis of the text including summary, key points, and insights.