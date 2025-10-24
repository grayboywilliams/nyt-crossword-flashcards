# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python project for scraping New York Times crossword clues from xwordinfo.com. The main script `nytwords.py` fetches clues for a specific word and saves them to CSV format.

## Dependencies

Required Python packages:
- `requests` - for HTTP requests to xwordinfo.com
- `beautifulsoup4` - for HTML parsing (install with `pip install beautifulsoup4`)
- `pandas` - for data manipulation and CSV export

Install missing dependencies:
```bash
pip install beautifulsoup4
```

## Running the Script

### Process Entire Wordlist (Default)
Process all words from `wordlist.csv` and save results to `output.csv`:

```bash
python3 nytwords.py
```

### Get Clues for a Single Word
Use the function directly in Python:

```python
from nytwords import get_clues_for_word

# Get 5 clues for "AREA" and print to console
get_clues_for_word("AREA", 5)
```

### Generate Fresh Wordlist
Create a new wordlist from the Popular page:

```bash
python3 nytwords.py --generate-wordlist
```

### Available Functions
- `generate_wordlist_from_popular(output_file="wordlist.csv", top_n=100)` - Generate wordlist from Popular page
- `get_clues_for_word(word, n_clues, session=None)` - Get clues for single word, prints to console
- `process_wordlist_csv(csv_file="wordlist.csv", output_file="output.csv")` - Process entire CSV
- `create_session()` - Create authenticated session for xwordinfo.com

## Data Files

- `wordlist.csv` - Input file with word statistics (Word, Clues, Occurrences, Rank)
- `output.csv` - Generated output with format (Word, Clue, Date, Rank, Occurrences)
- Script uses the "Clues" column from wordlist.csv to determine how many recent clues to fetch per word

## Notes

- Script establishes session by visiting xwordinfo.com main page and Popular page
- Only finds clues for words that have recent usage (2020-2025 timeframe)
- Words without recent clues will show "Could not find clues table" message
- Processing entire wordlist takes several minutes due to rate limiting

## Architecture

Simple single-file script that:
1. Makes HTTP request to xwordinfo.com with word parameter
2. Parses HTML table containing clue data
3. Extracts date and clue text for each occurrence
4. Saves most recent N clues to CSV using pandas