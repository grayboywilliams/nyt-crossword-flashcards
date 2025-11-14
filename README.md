# NYT Crossword Flashcards

A Python tool for scraping and generating flashcards from New York Times crossword clues using data from [xwordinfo.com](https://xwordinfo.com).

## Features

- **Scrape clues for specific words** - Get historical NYT crossword clues for any word
- **Generate wordlists** - Create custom wordlists from the most popular crossword words
- **Create flashcards** - Generate flashcards for common crossword clues with their most frequent answers
- **Batch processing** - Process entire wordlists and export to CSV

## Installation

### Requirements

- Python 3.x
- pip (Python package manager)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests beautifulsoup4 pandas
```

## Usage

### Process Entire Wordlist (Default)

Process all words from `wordlist.csv` and save results to `output.csv`:

```bash
python3 nytwords.py
```

### Generate Fresh Wordlist

Create a new wordlist from the Popular page on xwordinfo.com:

```bash
python3 nytwords.py --generate-wordlist
```

### Generate Common Clues Flashcards

Create flashcards for the most common crossword clues with their top 5 most-used answers:

```bash
# Generate flashcards for top 50 common clues (default)
python3 nytwords.py --common-clues

# Generate flashcards for top 100 common clues
python3 nytwords.py --common-clues 100
```

This creates `common_clues_flashcards.csv` with:
- **Clue** - The crossword clue (e.g., "Zip")
- **ClueCount** - Number of times the clue appears in NYT crosswords
- **TopAnswers** - Top 5 most-used answers with usage counts (e.g., "NIL (25), NADA (25), PEP (10)")
- **NumTopAnswers** - Number of top answers returned

Note: Cross-reference clues (e.g., "See 17-Across") are automatically filtered out.

### Use as a Python Module

```python
from nytwords import get_clues_for_word

# Get 5 clues for "AREA" and print to console
get_clues_for_word("AREA", 5)
```

## Available Functions

- `generate_wordlist_from_popular(output_file="wordlist.csv", top_n=100)` - Generate wordlist from Popular page
- `get_clues_for_word(word, n_clues, session=None)` - Get clues for a single word
- `process_wordlist_csv(csv_file="wordlist.csv", output_file="output.csv")` - Process entire CSV file
- `generate_common_clues_flashcards(output_file="common_clues_flashcards.csv", top_n=50, top_answers=5)` - Generate flashcards for common clues
- `get_common_clues(top_n=100, session=None)` - Get list of most common clues
- `get_answers_for_clue(clue, session=None, top_n=5)` - Search for top N most-used answers to a specific clue
- `create_session()` - Create authenticated session for xwordinfo.com

## Data Files

- **`wordlist.csv`** - Input file with word statistics (Word, Clues, Occurrences, Rank)
- **`output.csv`** - Generated output with format (Word, Clue, Date, Rank, Occurrences)
- **`common_clues_flashcards.csv`** - Generated flashcards (Clue, ClueCount, TopAnswers, NumTopAnswers)

## How It Works

1. Establishes a session by visiting xwordinfo.com main page and Popular page
2. Makes HTTP requests to xwordinfo.com with word/clue parameters
3. Parses HTML tables containing clue and answer data
4. Extracts dates, clues, and answer text for each occurrence
5. Saves results to CSV using pandas

## Notes

- Only finds clues for words with recent usage (2020-2025 timeframe)
- Words without recent clues will show "Could not find clues table" message
- Processing entire wordlists takes several minutes due to rate limiting
- Respects xwordinfo.com's rate limits to avoid server strain

## License

This project is for educational purposes. Please respect xwordinfo.com's terms of service when using this tool.

## Contributing

Feel free to submit issues or pull requests to improve this tool!
