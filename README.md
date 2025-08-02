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
```

Only the API key is mandatory. If model, temperature, or system_prompt are not specified, default values will be used (no system prompt by default).

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

## Supported Text Formats

- Plain text (.txt)
- Markdown (.md)
- Text from stdin

## Default Behavior

Without a custom prompt, Glean will provide a comprehensive analysis of the text including summary, key points, and insights.