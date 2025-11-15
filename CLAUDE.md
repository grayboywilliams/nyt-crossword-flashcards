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

### Generate Common Clues Flashcards
Create flashcards for the most common crossword clues with top 5 most-used answers:

```bash
# Generate flashcards for top 50 common clues (default)
python3 nytwords.py --common-clues

# Generate flashcards for top 100 common clues
python3 nytwords.py --common-clues 100
```

This will create a file `common_clues_flashcards.csv` with columns:
- `Clue` - The crossword clue (e.g., "Zip")
- `ClueCount` - Number of times the clue appears in NYT crosswords
- `TopAnswers` - Top 5 most-used answers with their usage counts (e.g., "NIL (25), NADA (25), PEP (10), NONE (7), SPED (5)")
- `NumTopAnswers` - Number of top answers returned (usually 5, may be less for rare clues)

Note: Cross-reference clues (e.g., "See 17-Across") are automatically filtered out.

### Generate Sports Teams Flashcards
Create flashcards for all major sports teams (MLB, NBA, NFL, NHL):

```bash
python3 nytwords.py --sports-teams
```

This will create a file `study/sports_teams_flashcards.csv` with bidirectional flashcards:
- Each team has 2 flashcard entries for versatile learning
- Direction 1: Team Name + Sport → City + Initials (e.g., "Lakers - NBA" → "Los Angeles - LAL")
- Direction 2: City + Initials → Team Name + Sport (e.g., "Los Angeles - LAL" → "Lakers - NBA")

Coverage:
- MLB: 30 teams (60 flashcards)
- NBA: 30 teams (60 flashcards)
- NFL: 32 teams (64 flashcards)
- NHL: 32 teams (64 flashcards)
- **Total: 124 teams, 248 flashcards**

### Available Functions
- `generate_wordlist_from_popular(output_file="wordlist.csv", top_n=100)` - Generate wordlist from Popular page
- `get_clues_for_word(word, n_clues, session=None)` - Get clues for single word, prints to console
- `process_wordlist_csv(csv_file="wordlist.csv", output_file="output.csv")` - Process entire CSV
- `generate_common_clues_flashcards(output_file="common_clues_flashcards.csv", top_n=50, top_answers=5)` - Generate flashcards for common clues with top N answers
- `generate_sports_teams_flashcards(output_file="study/sports_teams_flashcards.csv")` - Generate flashcards for all major sports teams (MLB, NBA, NFL, NHL)
- `get_common_clues(top_n=100, session=None)` - Get list of most common clues (filters out cross-references)
- `get_answers_for_clue(clue, session=None, top_n=5)` - Search for top N most-used answers to a specific clue
- `create_session()` - Create authenticated session for xwordinfo.com

## Data Files

- `wordlist.csv` - Input file with word statistics (Word, Clues, Occurrences, Rank)
- `output.csv` - Generated output with format (Word, Clue, Date, Rank, Occurrences)
- `study/common_clues_flashcards.csv` - Generated flashcards with format (Word, Clue, Date, Rank, Occurrences)
- `study/sports_teams_flashcards.csv` - Generated sports team flashcards with format (Word, Clue, Date, Rank, Occurrences)
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