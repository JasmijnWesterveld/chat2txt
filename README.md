# Chat to TXT Converter

A GUI application that converts CHAT format files (.cha) to TXT format with communication unit segmentation.

## Features

- Convert single .cha files or batch process entire folders
- Segment utterances into communication units (C-units)
- Optional Global Tales prompts detection and tagging
- Cross-platform support (macOS, Windows, Linux)
- Modern GUI built with CustomTkinter

## Requirements

- Python 3.7+
- customtkinter

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd chat2txt
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python -m chat2txt
```

Or:
```bash
python chat2txt/gui.py
```

### GUI Features

- **SELECT .CHA FILE**: Choose a single file to process
- **SELECT FOLDER**: Process all .cha files in a folder
- **ADD GLOBAL TALES PROMPTS**: Enable detection of emotional prompts (happy, angry, confused, proud, problem, important)
- **RUN CONVERSION**: Start the conversion process
- **OPEN FILE LOCATION**: Open the output folder in file explorer

## Input Format

The converter expects CHAT format with lines matching:
```
*PAR###: <utterance text> . <timestamp_code>
```

Where:
- `PAR###` is the participant number
- `<utterance text>` is the spoken text
- `<timestamp_code>` contains timing information with milliseconds

## Output Format

The converted TXT files include:
- C-units (communication units) prefixed with `C` or `E` (experimenter)
- Timestamps at the beginning and end
- Optional prompt tags (`+ prompt_name`) when enabled

## Project Structure

```
chat2txt/
├── chat2txt/
│   ├── __init__.py
│   ├── __main__.py
│   └── gui.py
├── README.md
├── requirements.txt
├── setup.py
├── .gitignore
└── .git/
```

## License

[Your License Here]
