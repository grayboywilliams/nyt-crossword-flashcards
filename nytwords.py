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

def generate_wordlist_from_popular(output_file="wordlist.csv", top_n=100):
    """
    Generate wordlist CSV from xwordinfo.com Popular page

    Args:
        output_file: Output CSV filename
        top_n: Number of top words to extract (default 100)
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
                        # Calculate clues count (count // 40)
                        clues = count // 40

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
    else:
        # Process existing wordlist to get clues
        process_wordlist_csv()
