import sqlite3
import json
import os
from typing import List, Dict, Optional, Union


class WordleHelper:
    def __init__(self, db_path: str = "wordle_words.db"):
        # Ensure the database is created in the same directory as this script
        if not os.path.isabs(db_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(script_dir, db_path)
        
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_table()
        
    def create_table(self):
        """Create words table if it doesn't exist"""
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                word TEXT UNIQUE NOT NULL,
                length INTEGER NOT NULL
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_length ON words(length)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_word ON words(word)')
        self.conn.commit()
    
    def load_words(self):
        """Load English words from local JSON file into database"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM words')
        word_count = cursor.fetchone()[0]
        
        if word_count > 0:
            print(f"Words already loaded in database ({word_count} words)")
            return
        
        print("⏳ Starting database creation process...")
            
        # Try to load from local JSON file first
        json_file_path = os.path.join(os.path.dirname(__file__), "words_dictionary_filtered.json")
        
        try:
            print(f"📖 Loading words from {json_file_path}")
            
            with open(json_file_path, 'r', encoding='utf-8') as file:
                # The JSON file might be in different formats
                data = json.load(file)
                
                if isinstance(data, dict):
                    # If it's a dictionary (word: definition format)
                    words = list(data.keys())
                elif isinstance(data, list):
                    # If it's a list of words
                    words = data
                else:
                    raise ValueError("Unsupported JSON format")
                    
            print(f"✅ Successfully loaded {len(words)} words from JSON file")
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading JSON file: {e}")
            # Fallback to basic word list
            words = [
                "about", "other", "which", "their", "would", "there", "could", "first",
                "water", "after", "where", "right", "think", "three", "years", "place",
                "sound", "great", "again", "still", "every", "small", "found", "those",
                "never", "under", "might", "while", "house", "world", "below", "asked",
                "going", "large", "until", "along", "shall", "being", "often", "earth",
                "began", "since", "study", "night", "light", "above", "paper", "parts",
                "young", "story", "point", "times", "heard", "whole", "white", "given",
                "means", "music", "miles", "thing", "today", "later", "using", "money",
                "lines", "order", "group", "among", "learn", "known", "space", "table",
                "early", "trees", "short", "hands", "state", "black", "shown", "stood",
                "front", "voice", "kinds", "makes", "comes", "close", "power", "lived",
                "vowel", "taken", "built", "heart", "ready", "quite", "class", "bring",
                "round", "horse", "shows", "piece", "green", "stand", "birds", "start",
                "river", "tried", "least", "field", "whose", "girls", "leave", "added",
                "color", "trade", "clear", "women", "light", "heard", "start", "moved"
            ]
            print("Using fallback word list")
        
        # Filter words by length and insert into database (load all word lengths, not just 5-letter words)
        print("🔄 Processing and filtering words...")
        
        all_valid_words = [word.upper() for word in words if word.isalpha() and len(word) >= 3]
        
        print("💾 Inserting words into database...")
        
        cursor.executemany(
            'INSERT OR IGNORE INTO words (word, length) VALUES (?, ?)',
            [(word, len(word)) for word in all_valid_words]
        )
        self.conn.commit()
        
        print("📊 Generating statistics...")
        
        # Count words by length for reporting
        length_counts = {}
        for word in all_valid_words:
            length = len(word)
            length_counts[length] = length_counts.get(length, 0) + 1
        
        print(f"✅ Loaded {len(all_valid_words)} total words into database:")
        for length in sorted(length_counts.keys()):
            print(f"  {length}-letter words: {length_counts[length]}")
        
        print("🎉 Database creation completed!")
    
    def filter_words(self, word_length: int = 5, known_letters: str = "", wrong_letters: str = "", 
                    wrong_positions: Optional[Dict[int, str]] = None) -> List[str]:
        """
        Filter words based on Wordle constraints
        
        Args:
            word_length: Length of words to search for (default: 5)
            known_letters: Pattern with known letters (use _ for unknown), e.g. "A_O__"
            wrong_letters: Letters not in the word, e.g. "XYZ"
            wrong_positions: Dict of {position: letter} for yellow letters, e.g. {1: 'A', 3: 'E'}
                Note: positions in wrong_positions are 1-based (first letter is position 1).
        """
        if wrong_positions is None:
            wrong_positions = {}
            
        cursor = self.conn.cursor()
        
        # Start with base query for specified word length
        query = "SELECT word FROM words WHERE length = ?"
        params: List[Union[int, str]] = [word_length]
        
        # Apply known letters pattern (green letters)
        if known_letters:
            pattern = known_letters.upper()
            if len(pattern) == word_length:
                for i, char in enumerate(pattern):
                    if char != '_':
                        query += f" AND SUBSTR(word, {i+1}, 1) = ?"
                        params.append(char)
        
        # Exclude wrong letters (gray letters)
        if wrong_letters:
            for letter in wrong_letters.upper():
                query += " AND word NOT LIKE ?"
                params.append(f"%{letter}%")
        
        # Handle yellow letters (wrong positions)
        for position, letter in wrong_positions.items():
            if 1 <= position <= word_length:  # Positions are 1-based
                # Letter must be in the word but not at this position
                query += f" AND word LIKE ? AND SUBSTR(word, {position}, 1) != ?"
                params.append(f"%{letter.upper()}%")
                params.append(letter.upper())
        
        cursor.execute(query, params)
        results = [row[0] for row in cursor.fetchall()]
        return results
    
    def get_letter_frequency(self, words: Optional[List[str]] = None, word_length: int = 5) -> Dict[str, int]:
        """Get frequency of letters in the word list"""
        if words is None:
            cursor = self.conn.cursor()
            cursor.execute("SELECT word FROM words WHERE length = ?", (word_length,))
            words = [row[0] for row in cursor.fetchall()]
        
        frequency = {}
        for word in words:
            for letter in word:
                frequency[letter] = frequency.get(letter, 0) + 1
        
        return dict(sorted(frequency.items(), key=lambda x: x[1], reverse=True))
    
    def suggest_best_words(self, filtered_words: List[str], top_n: int = 10) -> List[str]:
        """Suggest best words based on letter frequency"""
        if not filtered_words:
            return []
        
        frequency = self.get_letter_frequency(filtered_words)
        
        def word_score(word):
            # Score based on unique letters and their frequency
            unique_letters = set(word)
            return sum(frequency.get(letter, 0) for letter in unique_letters)
        
        scored_words = [(word, word_score(word)) for word in filtered_words]
        scored_words.sort(key=lambda x: x[1], reverse=True)
        
        return [word for word, score in scored_words[:top_n]]
    
    def close(self):
        """Close database connection"""
        self.conn.close()


def interactive_wordle_helper(helper: WordleHelper):
    """Interactive Wordle helper that asks for user input"""
    
    print("🎯 Welcome to the Interactive Wordle Helper! 🎯")
    print("=" * 50)
    
    try:
        # Store previous constraints
        prev_word_length = None
        prev_known_pattern = None
        prev_yellow_letters = None
        prev_wrong_letters = None

        # Initialize current constraints
        word_length = 5
        known_pattern = "_" * word_length
        yellow_letters = {}
        wrong_letters = ""

        while True:
            print("\nMain Menu:")
            print("1. Try a different word with different specs")
            print("2. Enter new specs")
            print("3. Max Coverage Guess (find word with max candidate letters)")
            print("4. Exit")
            choice = input("Enter choice (1/2/3/4, default: 2): ").strip()
            if choice == "4":
                break
            elif choice == "1":
                # Clear all previous inputs and start fresh
                prev_word_length = None
                prev_known_pattern = None
                prev_yellow_letters = None
                prev_wrong_letters = None
                continue
            elif choice == "3":
                # Max Coverage Guess mode
                print("\nEnter candidate words (comma or space separated, e.g. CRIED PRIED TRIED WRIED DRIED):")
                candidate_input = input("Candidates: ").strip().upper()
                if not candidate_input:
                    print("No candidates entered.")
                    continue
                # Split by comma or space
                candidates = [w.strip() for w in candidate_input.replace(",", " ").split() if w.strip()]
                if not candidates:
                    print("No valid candidates.")
                    continue
                # Get unique letters from all candidates
                candidate_letters = set()
                for word in candidates:
                    candidate_letters.update(set(word))
                print(f"Unique candidate letters: {', '.join(sorted(candidate_letters))}")
                # Ask for word length
                word_length_input = input(f"Word length (default: {len(candidates[0])}): ").strip()
                if not word_length_input:
                    wc_length = len(candidates[0])
                else:
                    try:
                        wc_length = int(word_length_input)
                    except ValueError:
                        print("Invalid word length, using default.")
                        wc_length = len(candidates[0])
                # Search for words with max candidate letter coverage
                cursor = helper.conn.cursor()
                cursor.execute("SELECT word FROM words WHERE length = ?", (wc_length,))
                all_words = [row[0] for row in cursor.fetchall()]
                def coverage_score(word):
                    return sum(1 for letter in set(word) if letter in candidate_letters)
                # Find max coverage score
                scored = [(word, coverage_score(word)) for word in all_words]
                if not scored:
                    print("No words found of that length.")
                    continue
                max_score = max(score for word, score in scored)
                # Filter to only max coverage words
                best_words = [word for word, score in scored if score == max_score]
                # Now, break ties by number of unknown letters used
                all_letters = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
                unknown_letters = all_letters - candidate_letters
                def unknown_count(word):
                    return sum(1 for letter in set(word) if letter in unknown_letters)
                best_words_with_unknowns = sorted(best_words, key=lambda w: (-unknown_count(w), w))
                # Show top 10
                print(f"\nWords with max coverage ({max_score} candidate letters), preferring unknowns:")
                for i, word in enumerate(best_words_with_unknowns[:10], 1):
                    print(f"  {i}. {word} (unknowns: {unknown_count(word)})")
                if len(best_words_with_unknowns) > 10:
                    print(f"  ... and {len(best_words_with_unknowns) - 10} more")
                print("\nReturn to main menu.")
                continue

            # Default: normal interactive mode
            # Only ask for word length if there is no previous word length (first run or after clearing)
            if prev_word_length is None and prev_known_pattern is None and prev_yellow_letters is None and prev_wrong_letters is None:
                prev_len_str = ""
                while True:
                    try:
                        word_length_input = input(f"\n1. How many letters in the word? (default: 5): ").strip()
                        if not word_length_input:
                            word_length = 5
                        else:
                            word_length = int(word_length_input)
                        if word_length > 0:
                            break
                        else:
                            print("Please enter a positive number.")
                    except ValueError:
                        print("Please enter a valid number.")
            else:
                word_length = prev_word_length if prev_word_length is not None else 5

            # 2. Ask for known letters (green letters with positions)
            # Accumulate known letter inputs step by step
            # Start with previous or blank pattern
            if prev_known_pattern is not None and len(prev_known_pattern) == word_length:
                known_pattern = prev_known_pattern
            else:
                known_pattern = "_" * (word_length if word_length is not None else 5)

            print(f"\n2. Enter known letters and their positions (GREEN letters):")
            print(f"   Format: Enter one or more letter-position pairs (e.g., 'A 1 O 3' or 'A1 O3'), or press Enter to finish.")
            print(f"   Current pattern: {known_pattern}")
            print(f"   Example for {word_length}-letter word: 'A 1 O 3' or 'A1 O3' builds 'A_O__'")

            while True:
                inp = input(f"   Enter letter(s) and position(s) (current: {known_pattern}): ").strip().upper()
                if not inp:
                    break
                # Split input into tokens (support both 'A1 O3' and 'A 1 O 3')
                tokens = inp.split()
                i = 0
                while i < len(tokens):
                    token = tokens[i]
                    # Handle 'A1', '_4', etc.
                    if (len(token) >= 2 and ((token[0].isalpha() and token[1:].isdigit()) or (token[0] == '_' and token[1:].isdigit()))):
                        letter = token[0]
                        pos = int(token[1:])
                        i += 1
                    # Handle 'A 1', '_ 4'
                    elif (i + 1 < len(tokens) and ((token.isalpha() or token == '_') and tokens[i+1].isdigit())):
                        letter = token
                        pos = int(tokens[i+1])
                        i += 2
                    else:
                        print("   Invalid format. Use 'LETTER POSITION' (e.g., 'A 1'), 'A1', '_ 4', or '_4'. Multiple pairs allowed.")
                        i += 1
                        continue
                    if 1 <= pos <= (word_length if word_length is not None else 5):
                        if letter == '_':
                            known_pattern = known_pattern[:pos-1] + '_' + known_pattern[pos:]
                            print(f"   Reset position {pos} to unknown (_). Updated pattern: {known_pattern}")
                        else:
                            known_pattern = known_pattern[:pos-1] + letter + known_pattern[pos:]
                            print(f"   Updated pattern: {known_pattern}")
                    else:
                        print(f"   Invalid position. Must be 1-{word_length if word_length is not None else 5}.")

            # 3. Ask for letters that are in the word but wrong position (yellow letters)
            prev_yellow_str = f" (previous: " + ", ".join([f"{v}{k}" for k, v in (prev_yellow_letters or {}).items()]) + ")" if prev_yellow_letters else ""
            print(f"\n3. Enter letters that are in the word but in wrong positions (YELLOW letters):{prev_yellow_str}")
            # Persist yellow letters across rounds
            yellow_letters = prev_yellow_letters.copy() if prev_yellow_letters else {}
            if yellow_letters:
                print(f"   Previous yellow letters: " + ", ".join([f"{v}{k}" for k, v in yellow_letters.items()]))
            print("   You can also remove a yellow letter by entering '-E4' or '-E 4'. Multiple pairs/removals allowed in one line.")

            while True:
                letter_input = input("   Enter letter(s) and wrong position(s) (e.g., 'A1 T3 -E4', or press Enter to finish): ").strip().upper()
                if not letter_input:
                    break
                tokens = letter_input.split()
                i = 0
                while i < len(tokens):
                    token = tokens[i]
                    try:
                        # Remove yellow letter constraint
                        if token.startswith('-'):
                            val = token[1:]
                            # Handle '-E4'
                            if len(val) >= 2 and val[0].isalpha() and val[1:].isdigit():
                                letter = val[0]
                                position = int(val[1:])
                                i += 1
                            # Handle '-E 4'
                            elif (i + 1 < len(tokens) and val.isalpha() and tokens[i+1].isdigit()):
                                letter = val
                                position = int(tokens[i+1])
                                i += 2
                            else:
                                print("   Invalid format for removal. Use '-LETTER POSITION' (e.g., '-E 4') or '-E4'.")
                                i += 1
                                continue
                            # Remove if exists
                            to_remove = [k for k, v in yellow_letters.items() if k == position and v == letter]
                            for k in to_remove:
                                yellow_letters.pop(k)
                            print(f"   Removed: {letter} is NOT in position {position}")
                            summary = ', '.join([f"{v}{k}" for k, v in yellow_letters.items()])
                            print(f"   incorrect positions: {summary if summary else '(none)'}")
                            continue
                        # Add yellow letter constraint
                        # Handle 'A1', 'T3'
                        if (len(token) >= 2 and token[0].isalpha() and token[1:].isdigit()):
                            letter = token[0]
                            position = int(token[1:])
                            i += 1
                        # Handle 'A 1'
                        elif (i + 1 < len(tokens) and token.isalpha() and tokens[i+1].isdigit()):
                            letter = token
                            position = int(tokens[i+1])
                            i += 2
                        else:
                            print("   Invalid format. Use 'LETTER POSITION' (e.g., 'A 1'), 'A1'. Multiple pairs/removals allowed.")
                            i += 1
                            continue
                        if 1 <= position <= (word_length if word_length is not None else 5) and letter.isalpha():
                            yellow_letters[position] = letter
                            print(f"   Added: {letter} is NOT in position {position}")
                            summary = ', '.join([f"{v}{k}" for k, v in yellow_letters.items()])
                            print(f"   incorrect positions: {summary}")
                        else:
                            print(f"   Invalid input. Position must be 1-{word_length if word_length is not None else 5} and letter must be alphabetic.")
                    except ValueError:
                        print("   Invalid format. Use 'LETTER POSITION' (e.g., 'A 1'), 'A1'. Multiple pairs/removals allowed.")

            # 4. Ask for letters not in the word (gray letters)
            prev_wrong_str = f" (previous: {prev_wrong_letters})" if prev_wrong_letters else ""
            print(f"\n4. Enter letters that are NOT in the word (GRAY letters):{prev_wrong_str}")
            print("   You can also remove a letter by entering '-X' (e.g., '-A')")
            wrong_letters_input = input("   Letters to exclude or remove (e.g., 'QWERTY', '-A')" + prev_wrong_str + ": ").strip().upper()
            # Start with previous excluded letters
            current_excluded = set(prev_wrong_letters) if prev_wrong_letters else set()
            if not wrong_letters_input:
                wrong_letters = ''.join(sorted(current_excluded))
            else:
                # Remove letters if input starts with '-', otherwise add
                # Support multiple removals, e.g., '-A', '-QW', etc.
                to_remove = set()
                to_add = set()
                for part in wrong_letters_input.split():
                    if part.startswith('-'):
                        to_remove.update([c for c in part[1:] if c.isalpha()])
                    else:
                        to_add.update([c for c in part if c.isalpha()])
                # Update the set
                current_excluded -= to_remove
                current_excluded |= to_add
                wrong_letters = ''.join(sorted(current_excluded))
            if wrong_letters:
                print(f"   excluded letters: {', '.join(wrong_letters)}")

            # Save constraints for next round
            prev_word_length = word_length
            prev_known_pattern = known_pattern
            prev_yellow_letters = yellow_letters.copy()
            prev_wrong_letters = wrong_letters

            # Filter words based on user input
            print(f"\n🔍 Searching for {word_length}-letter words...")

            # Modify the query for different word lengths
            cursor = helper.conn.cursor()
            query = f"SELECT word FROM words WHERE length = {word_length}"
            params = []

            # Apply known letters pattern (green letters)
            if known_pattern and known_pattern != "_" * (word_length if word_length is not None else 5):
                for i, char in enumerate(known_pattern):
                    if char != '_':
                        query += f" AND SUBSTR(word, {i+1}, 1) = ?"
                        params.append(char)

            # Exclude wrong letters (gray letters)
            if wrong_letters:
                for letter in wrong_letters:
                    if letter.isalpha():
                        query += " AND word NOT LIKE ?"
                        params.append(f"%{letter}%")

            # Handle yellow letters (wrong positions)
            for position, letter in yellow_letters.items():
                # Letter must be in the word but not at this position
                query += f" AND word LIKE ? AND SUBSTR(word, {position}, 1) != ?"
                params.append(f"%{letter}%")
                params.append(letter)

            cursor.execute(query, params)
            results = [row[0] for row in cursor.fetchall()]

            # Display results
            print(f"\n✅ Found {len(results)} matching words:")

            if results:
                # Calculate scores for all results
                frequency = helper.get_letter_frequency(results, word_length if word_length is not None else 5)

                # Use the suggest_best_words method for scoring and sorting
                best_words = helper.suggest_best_words(results, top_n=10)

                print("\nFirst 10 matches (sorted by score):")
                for i, word in enumerate(best_words, 1):
                    print(f"  {i:2d}. {word}")

                if len(results) > 10:
                    print(f"  ... and {len(results) - 10} more")

                # Show top 5 recommendations separately if there are many results
                if len(results) > 5:
                    print(f"\n⭐ Top 5 recommended words:")
                    # Calculate scores for top 5
                    top5 = best_words[:5]
                    word_scores = [(word, sum(frequency.get(letter, 0) for letter in set(word))) for word in top5]
                    for i, (word, score) in enumerate(word_scores, 1):
                        print(f"  {i}. {word} (score: {score})")
            else:
                print("❌ No words found matching your criteria.")
                print("💡 Try reducing the constraints or check for typos.")

            # Ask if user wants to try again
            print(f"\n" + "=" * 50)
            # Now offer options for next round
            # The loop will handle the choice
    except KeyboardInterrupt:
        print("\n\n👋 Thanks for using the Wordle Helper!")


def main(helper: WordleHelper):
    """Example usage of WordleHelper"""
    
    print("=== Wordle Helper Demo ===\n")
    
    # Example 1: No constraints
    print("1. All 5-letter words (first 10):")
    all_words = helper.filter_words(word_length=5)
    print(f"Total words: {len(all_words)}")
    print("First 10:", all_words[:10])
    print()
    
    # Example 2: Known letters (green)
    print("2. Words with pattern 'A_O__' (A in position 1, O in position 3):")
    pattern_words = helper.filter_words(word_length=5, known_letters="A_O__")
    print(f"Found {len(pattern_words)} words:")
    print(pattern_words[:10])
    print()
    
    # Example 3: Exclude letters (gray)
    print("3. Words without letters T, E, R:")
    no_ter_words = helper.filter_words(word_length=5, wrong_letters="TER")
    print(f"Found {len(no_ter_words)} words:")
    print(no_ter_words[:10])
    print()
    
    # Example 4: Yellow letters (wrong positions)
    print("4. Words containing A but not in position 1, and E but not in position 2:")
    yellow_words = helper.filter_words(word_length=5, wrong_positions={1: 'A', 2: 'E'})
    print(f"Found {len(yellow_words)} words:")
    print(yellow_words[:10])
    print()
    
    # Example 5: Complex scenario
    print("5. Complex scenario: Pattern '_O___', no T/E/R, A not in position 1:")
    complex_words = helper.filter_words(
        word_length=5,
        known_letters="_O___",
        wrong_letters="TER",
        wrong_positions={1: 'A'}
    )
    print(f"Found {len(complex_words)} words:")
    print(complex_words[:10])
    print()
    
    # Example 6: Best word suggestions
    print("6. Best word suggestions based on letter frequency:")
    if complex_words:
        best_words = helper.suggest_best_words(complex_words, 5)
        print("Top 5 suggested words:", best_words)
    else:
        print("No words found for the complex scenario")

    # Ask user if they want to use the interactive helper after demo
    again = input("\nWould you like to use the Interactive Wordle Helper? (y/n): ").strip().lower()
    if again.startswith('y'):
        interactive_wordle_helper(helper)


if __name__ == "__main__":
    print("Choose mode:")
    print("1. Interactive Wordle Helper")
    print("2. Demo mode (examples)")

    choice = input("Enter choice (1 or 2, default: 1): ").strip()

    print("\n🔄 Initializing Wordle Helper...")
    helper = WordleHelper()
    helper.load_words()

    try:
        if choice == "2":
            main(helper)
        else:
            interactive_wordle_helper(helper)
    finally:
        helper.close()
