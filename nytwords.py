import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def create_session():
    """Create and authenticate a session for xwordinfo.com"""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36 Edg/141.0.0.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1'
    }
    session.headers.update(headers)

    # Visit main page and Popular page to establish session
    session.get('https://www.xwordinfo.com/')
    session.headers.update({'Referer': 'https://www.xwordinfo.com/'})
    session.get('https://www.xwordinfo.com/Popular')
    session.headers.update({'Referer': 'https://www.xwordinfo.com/Popular'})

    return session

def get_clues_for_word(word, n_clues, session=None):
    """
    Get clues for a single word and print to console

    Args:
        word: The word to search for
        n_clues: Number of recent clues desired
        session: Optional existing session (will create new if None)
    """
    if session is None:
        session = create_session()
        print("Establishing session...")

    url = f"https://www.xwordinfo.com/Finder?word={word}"
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    # Find clues tables (look for any table with Date/Grid/Clue structure)
    tables = soup.find_all("table")
    clues_tables = []

    for table in tables:
        rows_in_table = table.find_all("tr")
        if len(rows_in_table) > 50:  # Main clues table should have many rows
            if rows_in_table:
                header_cells = rows_in_table[0].find_all(["td", "th"])
                header_text = [cell.get_text(strip=True).lower() for cell in header_cells]
                if "date" in header_text and "clue" in header_text:
                    clues_tables.append(table)

    # Prefer the table with most recent dates (2020+), but use any clues table if no recent one found
    clues_table = None
    for table in clues_tables:
        rows_in_table = table.find_all("tr")
        if len(rows_in_table) > 1:
            first_data_row = rows_in_table[1].find_all("td")
            if len(first_data_row) >= 1:
                first_date = first_data_row[0].get_text(strip=True)
                if any(year in first_date for year in ["2020", "2021", "2022", "2023", "2024", "2025"]):
                    clues_table = table
                    break

    # If no recent table found, use the first available clues table
    if clues_table is None and clues_tables:
        clues_table = clues_tables[0]

    clues = []
    if clues_table:
        table_rows = clues_table.find_all("tr")
        print(f"Found {len(table_rows)} rows for '{word}'")
        for tr in table_rows[1:n_clues+1]:  # skip header row, get n_clues
            tds = tr.find_all("td")
            if len(tds) >= 3:
                date = tds[0].get_text(strip=True)
                clue = tds[2].get_text(strip=True)
                # Remove suffix counts like "(19)", "(6)", etc. from clues
                import re
                clue = re.sub(r'\(\d+\)$', '', clue).strip()
                clues.append((date, clue))
                print(f"  {date}: {clue}")
    else:
        print(f"Could not find clues table for '{word}'")

    return clues

def generate_wordlist_from_popular(output_file="wordlist.csv", top_n=500, factor=80):
    """
    Generate wordlist CSV from xwordinfo.com Popular page

    Args:
        output_file: Output CSV filename
        top_n: Number of top words to extract
    """
    session = create_session()
    print("Fetching Popular page...")

    r = session.get('https://www.xwordinfo.com/Popular')
    soup = BeautifulSoup(r.text, "html.parser")

    # Find the main table with Rank, Count, Words
    table = soup.find("table")
    if not table:
        print("Error: Could not find Popular words table")
        return

    rows = table.find_all("tr")[1:]  # Skip header row
    wordlist_data = []

    for i, row in enumerate(rows):
        if len(wordlist_data) >= top_n:
            break

        cells = row.find_all("td")
        if len(cells) >= 3:
            rank_text = cells[0].get_text(strip=True)
            count_text = cells[1].get_text(strip=True)

            # Parse rank (remove trailing period)
            try:
                rank = int(rank_text.rstrip('.'))
            except ValueError:
                continue  # Skip if rank isn't a number

            # Parse count (should be integer)
            try:
                count = int(count_text)
            except ValueError:
                continue  # Skip if count isn't a number

            # Get individual words from links in the third cell
            word_links = cells[2].find_all("a")
            if word_links:
                # Process each word individually
                for link in word_links:
                    word_text = link.get_text(strip=True)
                    if word_text:  # Make sure word isn't empty
                        # Calculate clues count by scaling by factor
                        clues = count // factor

                        wordlist_data.append({
                            "Word": word_text,
                            "Clues": clues,
                            "Occurrences": count,
                            "Rank": rank
                        })

                        if len(wordlist_data) >= top_n:
                            break
            else:
                # Fallback to cell text if no links found
                word_text = cells[2].get_text(strip=True)
                if word_text:
                    clues = count // 40
                    wordlist_data.append({
                        "Word": word_text,
                        "Clues": clues,
                        "Occurrences": count,
                        "Rank": rank
                    })

    # Create DataFrame and save
    df = pd.DataFrame(wordlist_data)
    df.to_csv(output_file, index=False)

    print(f"Generated {len(wordlist_data)} words to {output_file}")
    print("Top 5 words:")
    print(df.head())

    return df

def get_common_clues(top_n=100, session=None):
    """
    Get the most common clues from xwordinfo.com

    Args:
        top_n: Number of top common clues to extract
        session: Optional existing session

    Returns:
        List of dictionaries with 'Clue' and 'Count'
    """
    if session is None:
        session = create_session()
        print("Establishing session...")

    print(f"Fetching common clues...")
    r = session.get('https://www.xwordinfo.com/CommonClues')
    soup = BeautifulSoup(r.text, "html.parser")

    # Find the main table
    table = soup.find("table")
    if not table:
        print("Error: Could not find common clues table")
        return []

    rows = table.find_all("tr")[1:]  # Skip header row
    common_clues = []

    for i, row in enumerate(rows):
        if len(common_clues) >= top_n:
            break

        cells = row.find_all("td")
        if len(cells) >= 2:
            clue_text = cells[0].get_text(strip=True)
            count_text = cells[1].get_text(strip=True)

            # Filter out cross-reference clues like "See 17-Across" or "See 5-Down"
            clue_lower = clue_text.lower()
            if "see" in clue_lower and ("across" in clue_lower or "down" in clue_lower):
                continue  # Skip cross-reference clues

            try:
                count = int(count_text)
                common_clues.append({
                    "Clue": clue_text,
                    "Count": count
                })
            except ValueError:
                continue  # Skip if count isn't a number

    print(f"Found {len(common_clues)} common clues (filtered out cross-reference clues)")
    return common_clues

def get_answers_for_clue(clue, session=None, top_n=5):
    """
    Search for all answers for a specific clue and return top N by frequency

    Args:
        clue: The clue text to search for
        session: Optional existing session
        top_n: Number of top answers to return (default 5)

    Returns:
        List of tuples (answer, count) sorted by frequency
    """
    if session is None:
        session = create_session()

    print(f"  Searching for answers to: '{clue}'")

    # Step 1: GET the search page to retrieve ViewState and other hidden fields
    url = "https://www.xwordinfo.com/SearchClues"
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    # Extract hidden form fields (required for ASP.NET)
    viewstate = soup.find("input", {"id": "__VIEWSTATE"})
    viewstate_gen = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})
    event_validation = soup.find("input", {"id": "__EVENTVALIDATION"})

    if not viewstate:
        print("    Warning: Could not find ViewState fields")
        return []

    # Step 2: POST the search with all required fields
    form_data = {
        '__VIEWSTATE': viewstate.get('value', ''),
        '__VIEWSTATEGENERATOR': viewstate_gen.get('value', '') if viewstate_gen else '',
        '__EVENTVALIDATION': event_validation.get('value', '') if event_validation else '',
        'ctl00$CPHContent$SearchPhrase': clue,
        'ctl00$CPHContent$rblCompare': 'Match complete clue',  # Search option
        'ctl00$CPHContent$SearchBut': 'Search'
    }

    r = session.post(url, data=form_data)
    soup = BeautifulSoup(r.text, "html.parser")

    # Check if we got redirected to login page
    page_title = soup.title.string.strip() if soup.title else ""
    if "login" in page_title.lower():
        print("    Session expired, re-establishing...")
        # Re-create the session
        session = create_session()
        # Retry the GET to get new ViewState
        r = session.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        viewstate = soup.find("input", {"id": "__VIEWSTATE"})
        viewstate_gen = soup.find("input", {"id": "__VIEWSTATEGENERATOR"})
        event_validation = soup.find("input", {"id": "__EVENTVALIDATION"})
        if viewstate:
            form_data = {
                '__VIEWSTATE': viewstate.get('value', ''),
                '__VIEWSTATEGENERATOR': viewstate_gen.get('value', '') if viewstate_gen else '',
                '__EVENTVALIDATION': event_validation.get('value', '') if event_validation else '',
                'ctl00$CPHContent$SearchPhrase': clue,
                'ctl00$CPHContent$rblCompare': 'Match complete clue',
                'ctl00$CPHContent$SearchBut': 'Search'
            }
            # Retry the POST
            r = session.post(url, data=form_data)
            soup = BeautifulSoup(r.text, "html.parser")

    # Step 3: Count answer occurrences
    from collections import Counter
    answer_counts = Counter()

    # Find all links that point to Finder (word lookup)
    all_links = soup.find_all("a", href=True)
    for link in all_links:
        if "Finder?word=" in link['href']:
            answer = link.get_text(strip=True)
            if answer and len(answer) > 0:  # Make sure it's not empty
                answer_counts[answer] += 1

    # Get top N most common answers
    top_answers = answer_counts.most_common(top_n)
    print(f"    Found {len(answer_counts)} unique answers, returning top {len(top_answers)}")
    return top_answers

def generate_common_clues_flashcards(output_file="study/common_clues_flashcards.csv", top_n=50, top_answers=5):
    """
    Generate flashcards for common clues with top most-used answers

    Args:
        output_file: Output CSV filename
        top_n: Number of top common clues to process
        top_answers: Number of top answers to include per clue (default 5)

    Returns:
        DataFrame with flashcard data
    """
    import os

    # Create session once for all requests
    session = create_session()

    # Step 1: Get list of common clues
    print(f"\nStep 1: Fetching top {top_n} common clues...")
    common_clues = get_common_clues(top_n=top_n, session=session)

    if not common_clues:
        print("Error: No common clues found")
        return None

    # Check if we have a partial file to resume from
    start_index = 0
    if os.path.exists(output_file):
        try:
            existing_df = pd.read_csv(output_file)
            start_index = len(existing_df)
            print(f"Resuming from clue {start_index + 1} (found {start_index} existing flashcards)")
        except:
            pass

    # Step 2: For each clue, find top answers by frequency
    print(f"\nStep 2: Finding top {top_answers} answers for each clue...")

    # Write header if starting fresh
    if start_index == 0:
        df_header = pd.DataFrame(columns=["Word", "Clue", "Date", "Rank", "Occurrences"])
        df_header.to_csv(output_file, index=False)

    for i in range(start_index, len(common_clues)):
        clue_info = common_clues[i]
        clue = clue_info["Clue"]
        clue_count = clue_info["Count"]

        print(f"\nProcessing clue {i+1}/{len(common_clues)} (count: {clue_count})")

        # Add delay to avoid rate limiting
        if i > 0:
            time.sleep(1)  # 1 second delay between requests

        try:
            # Get top answers for this clue (returns list of tuples: [(answer, count), ...])
            top_answer_list = get_answers_for_clue(clue, session=session, top_n=top_answers)

            if top_answer_list:
                # Format clue with answer hints: "Zip [3 letters (25x), 4 letters (25x), ...]"
                answer_hints = [f"{len(answer)} letters ({cnt}x)" for answer, cnt in top_answer_list]
                clue_with_hints = f"{clue} [{', '.join(answer_hints)}]"

                # Format answers for the back: "NIL (25), NADA (25), PEP (10), ..."
                answers_str = ", ".join([f"{answer} ({cnt})" for answer, cnt in top_answer_list])

                flashcard_row = {
                    "Word": answers_str,  # Back of card
                    "Clue": clue_with_hints,  # Front of card with hints
                    "Date": "-",
                    "Rank": i + 1,  # Position in the common clues list
                    "Occurrences": clue_count  # How many times this clue appears
                }

                # Append to CSV immediately
                df_row = pd.DataFrame([flashcard_row])
                df_row.to_csv(output_file, mode='a', header=False, index=False)
            else:
                print(f"    Warning: No answers found for '{clue}'")

        except Exception as e:
            print(f"    ERROR processing '{clue}': {e}")
            print(f"    Saved {i} flashcards so far. You can resume by running again.")
            # Don't re-raise - just continue to next clue
            continue

    # Step 3: Read final CSV
    print(f"\nStep 3: Loading final flashcards...")
    df = pd.read_csv(output_file)

    print(f"\nGenerated {len(df)} flashcards to {output_file}")
    print("\nSample flashcards:")
    print(df.head(10))

    return df

def generate_sports_teams_flashcards(output_file="study/sports_teams_flashcards.csv"):
    """
    Generate flashcards for major sports teams (MLB, NBA, NFL, NHL)

    Each team gets 2 flashcard entries for bidirectional learning:
    1. Clue: Team Name + Sport → Answer: City + Initials
    2. Clue: City + Initials → Answer: Team Name + Sport

    Args:
        output_file: Output CSV filename

    Returns:
        DataFrame with flashcard data
    """
    # Comprehensive sports teams data
    sports_teams = [
        # MLB Teams (30)
        {"city": "Arizona", "team": "Diamondbacks", "initials": "ARI", "sport": "MLB"},
        {"city": "Atlanta", "team": "Braves", "initials": "ATL", "sport": "MLB"},
        {"city": "Baltimore", "team": "Orioles", "initials": "BAL", "sport": "MLB"},
        {"city": "Boston", "team": "Red Sox", "initials": "BOS", "sport": "MLB"},
        {"city": "Chicago", "team": "Cubs", "initials": "CHC", "sport": "MLB"},
        {"city": "Chicago", "team": "White Sox", "initials": "CHW", "sport": "MLB"},
        {"city": "Cincinnati", "team": "Reds", "initials": "CIN", "sport": "MLB"},
        {"city": "Cleveland", "team": "Guardians", "initials": "CLE", "sport": "MLB"},
        {"city": "Colorado", "team": "Rockies", "initials": "COL", "sport": "MLB"},
        {"city": "Detroit", "team": "Tigers", "initials": "DET", "sport": "MLB"},
        {"city": "Houston", "team": "Astros", "initials": "HOU", "sport": "MLB"},
        {"city": "Kansas City", "team": "Royals", "initials": "KC", "sport": "MLB"},
        {"city": "Los Angeles", "team": "Angels", "initials": "LAA", "sport": "MLB"},
        {"city": "Los Angeles", "team": "Dodgers", "initials": "LAD", "sport": "MLB"},
        {"city": "Miami", "team": "Marlins", "initials": "MIA", "sport": "MLB"},
        {"city": "Milwaukee", "team": "Brewers", "initials": "MIL", "sport": "MLB"},
        {"city": "Minnesota", "team": "Twins", "initials": "MIN", "sport": "MLB"},
        {"city": "New York", "team": "Mets", "initials": "NYM", "sport": "MLB"},
        {"city": "New York", "team": "Yankees", "initials": "NYY", "sport": "MLB"},
        {"city": "Oakland", "team": "Athletics", "initials": "OAK", "sport": "MLB"},
        {"city": "Philadelphia", "team": "Phillies", "initials": "PHI", "sport": "MLB"},
        {"city": "Pittsburgh", "team": "Pirates", "initials": "PIT", "sport": "MLB"},
        {"city": "San Diego", "team": "Padres", "initials": "SD", "sport": "MLB"},
        {"city": "San Francisco", "team": "Giants", "initials": "SF", "sport": "MLB"},
        {"city": "Seattle", "team": "Mariners", "initials": "SEA", "sport": "MLB"},
        {"city": "St. Louis", "team": "Cardinals", "initials": "STL", "sport": "MLB"},
        {"city": "Tampa Bay", "team": "Rays", "initials": "TB", "sport": "MLB"},
        {"city": "Texas", "team": "Rangers", "initials": "TEX", "sport": "MLB"},
        {"city": "Toronto", "team": "Blue Jays", "initials": "TOR", "sport": "MLB"},
        {"city": "Washington", "team": "Nationals", "initials": "WSH", "sport": "MLB"},

        # NBA Teams (30)
        {"city": "Atlanta", "team": "Hawks", "initials": "ATL", "sport": "NBA"},
        {"city": "Boston", "team": "Celtics", "initials": "BOS", "sport": "NBA"},
        {"city": "Brooklyn", "team": "Nets", "initials": "BKN", "sport": "NBA"},
        {"city": "Charlotte", "team": "Hornets", "initials": "CHA", "sport": "NBA"},
        {"city": "Chicago", "team": "Bulls", "initials": "CHI", "sport": "NBA"},
        {"city": "Cleveland", "team": "Cavaliers", "initials": "CLE", "sport": "NBA"},
        {"city": "Dallas", "team": "Mavericks", "initials": "DAL", "sport": "NBA"},
        {"city": "Denver", "team": "Nuggets", "initials": "DEN", "sport": "NBA"},
        {"city": "Detroit", "team": "Pistons", "initials": "DET", "sport": "NBA"},
        {"city": "Golden State", "team": "Warriors", "initials": "GSW", "sport": "NBA"},
        {"city": "Houston", "team": "Rockets", "initials": "HOU", "sport": "NBA"},
        {"city": "Indiana", "team": "Pacers", "initials": "IND", "sport": "NBA"},
        {"city": "Los Angeles", "team": "Clippers", "initials": "LAC", "sport": "NBA"},
        {"city": "Los Angeles", "team": "Lakers", "initials": "LAL", "sport": "NBA"},
        {"city": "Memphis", "team": "Grizzlies", "initials": "MEM", "sport": "NBA"},
        {"city": "Miami", "team": "Heat", "initials": "MIA", "sport": "NBA"},
        {"city": "Milwaukee", "team": "Bucks", "initials": "MIL", "sport": "NBA"},
        {"city": "Minnesota", "team": "Timberwolves", "initials": "MIN", "sport": "NBA"},
        {"city": "New Orleans", "team": "Pelicans", "initials": "NOP", "sport": "NBA"},
        {"city": "New York", "team": "Knicks", "initials": "NYK", "sport": "NBA"},
        {"city": "Oklahoma City", "team": "Thunder", "initials": "OKC", "sport": "NBA"},
        {"city": "Orlando", "team": "Magic", "initials": "ORL", "sport": "NBA"},
        {"city": "Philadelphia", "team": "76ers", "initials": "PHI", "sport": "NBA"},
        {"city": "Phoenix", "team": "Suns", "initials": "PHX", "sport": "NBA"},
        {"city": "Portland", "team": "Trail Blazers", "initials": "POR", "sport": "NBA"},
        {"city": "Sacramento", "team": "Kings", "initials": "SAC", "sport": "NBA"},
        {"city": "San Antonio", "team": "Spurs", "initials": "SAS", "sport": "NBA"},
        {"city": "Toronto", "team": "Raptors", "initials": "TOR", "sport": "NBA"},
        {"city": "Utah", "team": "Jazz", "initials": "UTA", "sport": "NBA"},
        {"city": "Washington", "team": "Wizards", "initials": "WAS", "sport": "NBA"},

        # NFL Teams (32)
        {"city": "Arizona", "team": "Cardinals", "initials": "ARI", "sport": "NFL"},
        {"city": "Atlanta", "team": "Falcons", "initials": "ATL", "sport": "NFL"},
        {"city": "Baltimore", "team": "Ravens", "initials": "BAL", "sport": "NFL"},
        {"city": "Buffalo", "team": "Bills", "initials": "BUF", "sport": "NFL"},
        {"city": "Carolina", "team": "Panthers", "initials": "CAR", "sport": "NFL"},
        {"city": "Chicago", "team": "Bears", "initials": "CHI", "sport": "NFL"},
        {"city": "Cincinnati", "team": "Bengals", "initials": "CIN", "sport": "NFL"},
        {"city": "Cleveland", "team": "Browns", "initials": "CLE", "sport": "NFL"},
        {"city": "Dallas", "team": "Cowboys", "initials": "DAL", "sport": "NFL"},
        {"city": "Denver", "team": "Broncos", "initials": "DEN", "sport": "NFL"},
        {"city": "Detroit", "team": "Lions", "initials": "DET", "sport": "NFL"},
        {"city": "Green Bay", "team": "Packers", "initials": "GB", "sport": "NFL"},
        {"city": "Houston", "team": "Texans", "initials": "HOU", "sport": "NFL"},
        {"city": "Indianapolis", "team": "Colts", "initials": "IND", "sport": "NFL"},
        {"city": "Jacksonville", "team": "Jaguars", "initials": "JAX", "sport": "NFL"},
        {"city": "Kansas City", "team": "Chiefs", "initials": "KC", "sport": "NFL"},
        {"city": "Las Vegas", "team": "Raiders", "initials": "LV", "sport": "NFL"},
        {"city": "Los Angeles", "team": "Chargers", "initials": "LAC", "sport": "NFL"},
        {"city": "Los Angeles", "team": "Rams", "initials": "LAR", "sport": "NFL"},
        {"city": "Miami", "team": "Dolphins", "initials": "MIA", "sport": "NFL"},
        {"city": "Minnesota", "team": "Vikings", "initials": "MIN", "sport": "NFL"},
        {"city": "New England", "team": "Patriots", "initials": "NE", "sport": "NFL"},
        {"city": "New Orleans", "team": "Saints", "initials": "NO", "sport": "NFL"},
        {"city": "New York", "team": "Giants", "initials": "NYG", "sport": "NFL"},
        {"city": "New York", "team": "Jets", "initials": "NYJ", "sport": "NFL"},
        {"city": "Philadelphia", "team": "Eagles", "initials": "PHI", "sport": "NFL"},
        {"city": "Pittsburgh", "team": "Steelers", "initials": "PIT", "sport": "NFL"},
        {"city": "San Francisco", "team": "49ers", "initials": "SF", "sport": "NFL"},
        {"city": "Seattle", "team": "Seahawks", "initials": "SEA", "sport": "NFL"},
        {"city": "Tampa Bay", "team": "Buccaneers", "initials": "TB", "sport": "NFL"},
        {"city": "Tennessee", "team": "Titans", "initials": "TEN", "sport": "NFL"},
        {"city": "Washington", "team": "Commanders", "initials": "WAS", "sport": "NFL"},

        # NHL Teams (32)
        {"city": "Anaheim", "team": "Ducks", "initials": "ANA", "sport": "NHL"},
        {"city": "Arizona", "team": "Coyotes", "initials": "ARI", "sport": "NHL"},
        {"city": "Boston", "team": "Bruins", "initials": "BOS", "sport": "NHL"},
        {"city": "Buffalo", "team": "Sabres", "initials": "BUF", "sport": "NHL"},
        {"city": "Calgary", "team": "Flames", "initials": "CGY", "sport": "NHL"},
        {"city": "Carolina", "team": "Hurricanes", "initials": "CAR", "sport": "NHL"},
        {"city": "Chicago", "team": "Blackhawks", "initials": "CHI", "sport": "NHL"},
        {"city": "Colorado", "team": "Avalanche", "initials": "COL", "sport": "NHL"},
        {"city": "Columbus", "team": "Blue Jackets", "initials": "CBJ", "sport": "NHL"},
        {"city": "Dallas", "team": "Stars", "initials": "DAL", "sport": "NHL"},
        {"city": "Detroit", "team": "Red Wings", "initials": "DET", "sport": "NHL"},
        {"city": "Edmonton", "team": "Oilers", "initials": "EDM", "sport": "NHL"},
        {"city": "Florida", "team": "Panthers", "initials": "FLA", "sport": "NHL"},
        {"city": "Los Angeles", "team": "Kings", "initials": "LAK", "sport": "NHL"},
        {"city": "Minnesota", "team": "Wild", "initials": "MIN", "sport": "NHL"},
        {"city": "Montreal", "team": "Canadiens", "initials": "MTL", "sport": "NHL"},
        {"city": "Nashville", "team": "Predators", "initials": "NSH", "sport": "NHL"},
        {"city": "New Jersey", "team": "Devils", "initials": "NJD", "sport": "NHL"},
        {"city": "New York", "team": "Islanders", "initials": "NYI", "sport": "NHL"},
        {"city": "New York", "team": "Rangers", "initials": "NYR", "sport": "NHL"},
        {"city": "Ottawa", "team": "Senators", "initials": "OTT", "sport": "NHL"},
        {"city": "Philadelphia", "team": "Flyers", "initials": "PHI", "sport": "NHL"},
        {"city": "Pittsburgh", "team": "Penguins", "initials": "PIT", "sport": "NHL"},
        {"city": "San Jose", "team": "Sharks", "initials": "SJS", "sport": "NHL"},
        {"city": "Seattle", "team": "Kraken", "initials": "SEA", "sport": "NHL"},
        {"city": "St. Louis", "team": "Blues", "initials": "STL", "sport": "NHL"},
        {"city": "Tampa Bay", "team": "Lightning", "initials": "TBL", "sport": "NHL"},
        {"city": "Toronto", "team": "Maple Leafs", "initials": "TOR", "sport": "NHL"},
        {"city": "Vancouver", "team": "Canucks", "initials": "VAN", "sport": "NHL"},
        {"city": "Vegas", "team": "Golden Knights", "initials": "VGK", "sport": "NHL"},
        {"city": "Washington", "team": "Capitals", "initials": "WSH", "sport": "NHL"},
        {"city": "Winnipeg", "team": "Jets", "initials": "WPG", "sport": "NHL"},
    ]

    print(f"Generating sports team flashcards for {len(sports_teams)} teams...")

    flashcards = []

    for i, team in enumerate(sports_teams):
        # Flashcard 1: Team Name + Sport → City + Initials
        flashcards.append({
            "Word": f"{team['city']} - {team['initials']}",  # Answer
            "Clue": f"{team['team']} - {team['sport']}",      # Clue
            "Date": "-",
            "Rank": i * 2 + 1,
            "Occurrences": 1
        })

        # Flashcard 2: City + Initials → Team Name + Sport (reverse)
        flashcards.append({
            "Word": f"{team['team']} - {team['sport']}",      # Answer
            "Clue": f"{team['city']} - {team['initials']}",   # Clue
            "Date": "-",
            "Rank": i * 2 + 2,
            "Occurrences": 1
        })

    # Create DataFrame and save
    df = pd.DataFrame(flashcards)

    # Ensure output directory exists
    import os
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    df.to_csv(output_file, index=False)

    print(f"\nGenerated {len(flashcards)} flashcards ({len(sports_teams)} teams × 2 directions)")
    print(f"Saved to {output_file}")
    print(f"\nBreakdown by sport:")
    for sport in ["MLB", "NBA", "NFL", "NHL"]:
        count = len([t for t in sports_teams if t['sport'] == sport])
        print(f"  {sport}: {count} teams ({count * 2} flashcards)")

    print(f"\nSample flashcards:")
    print(df.head(10))

    return df

def process_wordlist_csv(csv_file="wordlist.csv", output_file="output.csv"):
    """
    Process entire wordlist CSV and output results to CSV file

    Args:
        csv_file: Input CSV file with Word,Clues,Occurrences,Rank columns
        output_file: Output CSV file
    """
    # Load wordlist
    try:
        wordlist_df = pd.read_csv(csv_file)
        print(f"Loaded {len(wordlist_df)} words from {csv_file}")
    except FileNotFoundError:
        print(f"Error: {csv_file} not found")
        return

    # Create session once for all requests
    session = create_session()
    print("Establishing session...")

    all_results = []

    for index, row in wordlist_df.iterrows():
        word = row["Word"]
        rank = row["Rank"]
        occurrences = row["Occurrences"]
        target_clues = row["Clues"]  # Use the number from the CSV

        print(f"\nProcessing word {index+1}/{len(wordlist_df)}: {word} (targeting {target_clues} clues)")

        # Add delay to avoid rate limiting
        if index > 0:  # No delay for first word
            time.sleep(1)  # 1 second delay between requests

        url = f"https://www.xwordinfo.com/Finder?word={word}"
        r = session.get(url)

        # Check response status
        if r.status_code != 200:
            print(f"  ERROR: HTTP {r.status_code} for {word}")
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Check if we got redirected to login page
        page_title = soup.title.string.strip() if soup.title else ""
        if "login" in page_title.lower():
            print(f"  ERROR: Redirected to login page for {word}")
            # Try to re-establish session
            session = create_session()
            print("  Re-establishing session...")
            r = session.get(url)
            soup = BeautifulSoup(r.text, "html.parser")

        # Find clues tables (look for any table with Date/Grid/Clue structure)
        tables = soup.find_all("table")
        clues_tables = []

        for table in tables:
            rows_in_table = table.find_all("tr")
            if len(rows_in_table) > 50:  # Main clues table should have many rows
                if rows_in_table:
                    header_cells = rows_in_table[0].find_all(["td", "th"])
                    header_text = [cell.get_text(strip=True).lower() for cell in header_cells]
                    if "date" in header_text and "clue" in header_text:
                        clues_tables.append(table)

        # Debug for words that might be failing
        if len(clues_tables) == 0:
            print(f"  DEBUG: No clues tables found for {word}. Found {len(tables)} total tables.")
            if len(tables) > 0:
                print(f"  DEBUG: Table sizes: {[len(t.find_all('tr')) for t in tables]}")

        # Prefer the table with most recent dates (2020+), but use any clues table if no recent one found
        clues_table = None
        for table in clues_tables:
            rows_in_table = table.find_all("tr")
            if len(rows_in_table) > 1:
                first_data_row = rows_in_table[1].find_all("td")
                if len(first_data_row) >= 1:
                    first_date = first_data_row[0].get_text(strip=True)
                    if any(year in first_date for year in ["2020", "2021", "2022", "2023", "2024", "2025"]):
                        clues_table = table
                        break

        # If no recent table found, use the first available clues table
        if clues_table is None and clues_tables:
            clues_table = clues_tables[0]

        if clues_table:
            table_rows = clues_table.find_all("tr")
            clues_found = 0
            for tr in table_rows[1:target_clues+1]:  # skip header row, get target number
                tds = tr.find_all("td")
                if len(tds) >= 3:
                    date = tds[0].get_text(strip=True)
                    clue = tds[2].get_text(strip=True)
                    # Remove suffix counts like "(19)", "(6)", etc. from clues
                    import re
                    clue = re.sub(r'\(\d+\)$', '', clue).strip()
                    all_results.append({
                        "Word": word,
                        "Clue": clue,
                        "Date": date,
                        "Rank": rank,
                        "Occurrences": occurrences
                    })
                    clues_found += 1
            print(f"  Found {clues_found} clues")
        else:
            print(f"  Could not find clues table for '{word}'")

    # Save all results
    df = pd.DataFrame(all_results)
    df.to_csv(output_file, index=False)
    print(f"\nSaved {len(all_results)} total clues to {output_file}")
    return df

# Main execution
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--generate-wordlist":
        # Generate fresh wordlist from Popular page
        generate_wordlist_from_popular()
    elif len(sys.argv) > 1 and sys.argv[1] == "--common-clues":
        # Generate flashcards for common clues
        # Optional: specify number of clues (default 50)
        top_n = 50
        if len(sys.argv) > 2:
            try:
                top_n = int(sys.argv[2])
            except ValueError:
                print("Error: Second argument must be a number")
                sys.exit(1)
        generate_common_clues_flashcards(top_n=top_n)
    elif len(sys.argv) > 1 and sys.argv[1] == "--sports-teams":
        # Generate flashcards for major sports teams (MLB, NBA, NFL, NHL)
        generate_sports_teams_flashcards()
    else:
        # Process existing wordlist to get clues
        process_wordlist_csv()
