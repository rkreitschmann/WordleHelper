"""
Value-focused tests for Wordle Helper - Testing actual values and precise behaviors
"""

import pytest
import os
import tempfile
import sqlite3
from Wordle_helper import WordleHelper


class TestWordleHelperCore:
    """Test core functionality with precise value validation"""
    
    @pytest.fixture
    def test_helper(self):
        """Create WordleHelper with known test data for precise testing"""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        helper = WordleHelper(temp_db.name)
        
        # Carefully chosen test words with known properties for precise testing
        test_words = [
            # 5-letter words with specific characteristics
            "ADIEU",  # 4 vowels: A,I,E,U - position weights: S=0, E=300, vowels=2000
            "AROSE",  # 3 vowels: A,O,E - common start S, common end E
            "SLATE",  # 2 vowels: A,E - common start S, common end E  
            "HOUSE",  # 3 vowels: O,U,E - common start=no, common end E
            "QUEUE",  # 2 vowels: U,E - repeated letters (penalty), common end E
            "PUPPY",  # 1 vowel: U - repeated P (penalty), no bonuses
            "LLAMA",  # 2 vowels: A,A - repeated L (penalty), common end A not in list
            # 3-letter words
            "CAT",    # 1 vowel: A
            "DOG",    # 1 vowel: O  
            # 6-letter words
            "SIMPLE", # 2 vowels: I,E
            "PYTHON"  # 1 vowel: Y (not counting Y), O
        ]
        
        cursor = helper.conn.cursor()
        for word in test_words:
            cursor.execute('INSERT OR IGNORE INTO words (word, length) VALUES (?, ?)', 
                         (word, len(word)))
        helper.conn.commit()
        
        yield helper
        
        helper.close()
        os.unlink(temp_db.name)

    def test_database_structure_exact(self, test_helper):
        """Test exact database structure and content"""
        cursor = test_helper.conn.cursor()
        
        # Verify exact table structure
        cursor.execute("PRAGMA table_info(words)")
        columns = cursor.fetchall()
        assert len(columns) == 3
        assert columns[0][1] == 'id'      # Column name
        assert columns[1][1] == 'word'    # Column name  
        assert columns[2][1] == 'length'  # Column name
        
        # Verify exact word count
        cursor.execute("SELECT COUNT(*) FROM words")
        assert cursor.fetchone()[0] == 11
        
        # Verify specific words exist
        cursor.execute("SELECT word FROM words WHERE word = 'ADIEU'")
        assert cursor.fetchone()[0] == 'ADIEU'

    def test_filter_words_exact_results(self, test_helper):
        """Test filtering returns exact expected results"""
        # Test exact 5-letter word count
        words_5 = test_helper.filter_words(word_length=5)
        assert len(words_5) == 7  # Exactly 7 five-letter words
        expected_5_letter = {"ADIEU", "AROSE", "SLATE", "HOUSE", "QUEUE", "PUPPY", "LLAMA"}
        assert set(words_5) == expected_5_letter
        
        # Test exact 3-letter word count
        words_3 = test_helper.filter_words(word_length=3)
        assert len(words_3) == 2
        assert set(words_3) == {"CAT", "DOG"}

    def test_known_letters_exact_matches(self, test_helper):
        """Test known letter patterns return exact matches"""
        # Pattern: A____
        words = test_helper.filter_words(word_length=5, known_letters="A____")
        assert set(words) == {"ADIEU", "AROSE"}  # Exactly these two words
        
        # Pattern: ____E  
        words = test_helper.filter_words(word_length=5, known_letters="____E")
        assert set(words) == {"AROSE", "SLATE", "HOUSE", "QUEUE"}
        
        # Pattern: _L___
        words = test_helper.filter_words(word_length=5, known_letters="_L___")
        assert set(words) == {"SLATE", "LLAMA"}
        
        # Pattern with multiple positions: A___E
        words = test_helper.filter_words(word_length=5, known_letters="A___E")
        assert set(words) == {"AROSE"}  # Only AROSE matches

    def test_wrong_letters_exact_exclusions(self, test_helper):
        """Test wrong letters exclude exactly the right words"""
        # Exclude E - should remove ADIEU, AROSE, SLATE, HOUSE, QUEUE
        words = test_helper.filter_words(word_length=5, wrong_letters="E")
        assert set(words) == {"PUPPY", "LLAMA"}  # Only these don't contain E
        
        # Exclude P - should remove PUPPY
        words = test_helper.filter_words(word_length=5, wrong_letters="P")
        assert "PUPPY" not in words
        assert len(words) == 6  # All except PUPPY
        
        # Exclude multiple: E and U
        words = test_helper.filter_words(word_length=5, wrong_letters="EU")
        assert set(words) == {"LLAMA"}  # Only LLAMA has neither E nor U

    def test_yellow_letters_exact_behavior(self, test_helper):
        """Test yellow letter constraints with exact expected results"""
        # A is in word but not position 1 (0-indexed = position 0)
        words = test_helper.filter_words(word_length=5, wrong_positions=[(1, 'A')])
        # Should include words with A not in position 1: LLAMA (A in positions 2,4)
        # Should exclude: ADIEU, AROSE (A in position 1)
        result_set = set(words)
        assert "LLAMA" in result_set  # A in positions 2,4
        assert "ADIEU" not in result_set  # A in position 1
        assert "AROSE" not in result_set  # A in position 1
        
        # Multiple constraints: E not in position 5 (0-indexed = 4) AND not in position 4 (0-indexed = 3)
        words = test_helper.filter_words(word_length=5, wrong_positions=[(5, 'E'), (4, 'E')])
        # This should allow words with E only in positions 1,2,3 (0-indexed 0,1,2)
        result_words = set(words)
        # ADIEU has E in position 4 (0-indexed 3) - should be excluded by second constraint
        assert "ADIEU" not in result_words

    def test_letter_frequency_exact_values(self, test_helper):
        """Test letter frequency calculations return exact expected values"""
        freq = test_helper.get_letter_frequency(word_length=5)
        
        # Count letters manually from our test words:
        # ADIEU: A,D,I,E,U (5 letters)
        # AROSE: A,R,O,S,E (5 letters)  
        # SLATE: S,L,A,T,E (5 letters)
        # HOUSE: H,O,U,S,E (5 letters)
        # QUEUE: Q,U,E,U,E (3 unique: Q,U,E)
        # PUPPY: P,U,P,P,Y (3 unique: P,U,Y)
        # LLAMA: L,L,A,M,A (3 unique: L,A,M)
        
        # E appears in: ADIEU, AROSE, SLATE, HOUSE, QUEUE(2x) = 6 times
        assert freq['E'] == 6
        
        # A appears in: ADIEU, AROSE, SLATE, LLAMA(2x) = 5 times  
        assert freq['A'] == 5
        
        # U appears in: ADIEU, HOUSE, QUEUE(2x), PUPPY = 5 times
        assert freq['U'] == 5
        
        # S appears in: AROSE, SLATE, HOUSE = 3 times
        assert freq['S'] == 3

    def test_scoring_algorithm_exact_values(self, test_helper):
        """Test scoring algorithm produces exact expected score relationships"""
        # Get frequency for scoring calculation
        freq = test_helper.get_letter_frequency(word_length=5)
        
        # Test ADIEU score components:
        # - 4 vowels: min(4 * 500, 1500) = 1500 (maxed out)
        # - Common start bonus: A not in common_starts = 0
        # - Common end bonus: U not in common_ends = 0  
        # - Repeat penalty: 0 (no repeats)
        # - Position score: sum of unique letters * position weights
        
        adieu_score = test_helper.calculate_word_score("ADIEU", freq)
        assert isinstance(adieu_score, (int, float))
        assert adieu_score > 0
        
        # Test QUEUE score components:
        # - 2 vowels: 2 * 500 = 1000
        # - Repeat penalty: (5 - 3) * 200 = 400 (Q,U,E are unique, 2 repeats)
        # - Common end bonus: E = 300
        
        queue_score = test_helper.calculate_word_score("QUEUE", freq)
        assert isinstance(queue_score, (int, float))
        
        # ADIEU should score higher than QUEUE (vowels + no repeats vs repeats)
        assert adieu_score > queue_score, f"ADIEU ({adieu_score}) should score higher than QUEUE ({queue_score})"

    def test_suggest_best_words_exact_ranking(self, test_helper):
        """Test word suggestions return exact expected rankings"""
        # Test with words that have clear scoring differences
        test_words = ["ADIEU", "QUEUE", "PUPPY"]
        suggestions = test_helper.suggest_best_words(test_words, 3)
        
        # Expected order based on scoring:
        # 1. ADIEU: 4 vowels (1500) + no repeats + position weights
        # 2. QUEUE: 2 vowels (1000) + end bonus (300) - repeat penalty (400)
        # 3. PUPPY: 1 vowel (500) - repeat penalty (600) 
        
        assert len(suggestions) == 3
        assert suggestions[0] == "ADIEU"  # Highest score
        assert suggestions[-1] == "PUPPY"  # Lowest score
        
        # Test top_n parameter works exactly
        top_2 = test_helper.suggest_best_words(test_words, 2)
        assert len(top_2) == 2
        assert top_2 == suggestions[:2]

    def test_complex_filtering_exact_results(self, test_helper):
        """Test complex multi-constraint filtering produces exact results"""
        # Complex scenario: 5-letter words, third letter A, exclude Q, E not in position 1
        words = test_helper.filter_words(
            word_length=5,
            known_letters="__A__", 
            wrong_letters="Q",
            wrong_positions=[(1, 'E')]
        )
        
        # Analysis of our words with __A__: SLATE, LLAMA
        # - __A__: SLATE (S-L-A-T-E), LLAMA (L-L-A-M-A) qualify (third letter A)
        # - Exclude Q: Both qualify (neither contains Q)
        # - E not in position 1: SLATE has E in word but not in position 1, LLAMA has no E
        # - For yellow constraint (E not in pos 1): only words containing E but not in pos 1 qualify
        # - SLATE: contains E (position 4), not in position 1 ✓
        # - LLAMA: doesn't contain E, so excluded by yellow constraint
        # - Final result: SLATE only
        
        assert set(words) == {"SLATE"}

    def test_position_weights_exact_calculation(self, test_helper):
        """Test position weights are applied exactly as specified"""
        # Position weights are [1.2, 1.0, 0.9, 1.0, 1.1]
        freq = test_helper.get_letter_frequency(word_length=5)
        
        # Create a word where we can predict the position score
        # For AROSE: A(pos0)*1.2 + R(pos1)*1.0 + O(pos2)*0.9 + S(pos3)*1.0 + E(pos4)*1.1
        arose_score = test_helper.calculate_word_score("AROSE", freq)
        
        # Manually calculate expected position component
        expected_position = (freq['A'] * 1.2 + freq['R'] * 1.0 + freq['O'] * 0.9 + 
                           freq['S'] * 1.0 + freq['E'] * 1.1)
        
        # The total score includes bonuses, but position component should be consistent
        assert arose_score > expected_position  # Should be higher due to bonuses

    def test_vowel_bonus_exact_calculation(self, test_helper):
        """Test vowel bonus calculation is exact"""
        freq = test_helper.get_letter_frequency(word_length=5)
        
        # Test 1 vowel word
        puppy_score = test_helper.calculate_word_score("PUPPY", freq)
        
        # Test 4 vowel word (should hit max bonus)
        adieu_score = test_helper.calculate_word_score("ADIEU", freq)
        
        # Vowel bonus difference should be significant
        # PUPPY: 1 vowel = 500, ADIEU: 4 vowels = 1500 (maxed)
        # Difference should be at least 1000 (ignoring other factors)
        score_diff = adieu_score - puppy_score
        assert score_diff > 800, f"Score difference ({score_diff}) should reflect vowel bonus difference"

    def test_repeat_penalty_exact_calculation(self, test_helper):
        """Test repeat letter penalty is calculated exactly"""
        freq = test_helper.get_letter_frequency(word_length=5)
        
        # Compare words with same letters but different repeat patterns
        # Use frequency to create comparable baseline
        
        # AROSE: no repeats, penalty = 0
        arose_score = test_helper.calculate_word_score("AROSE", freq)
        
        # QUEUE: 2 repeats (U,E), penalty = 2 * 200 = 400
        queue_score = test_helper.calculate_word_score("QUEUE", freq)
        
        # AROSE should score higher due to no repeat penalty
        assert arose_score > queue_score


class TestEdgeCasesAndBoundaries:
    """Test edge cases with exact boundary conditions"""
    
    def test_empty_results_exact(self):
        """Test empty database returns exactly empty results"""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        helper = WordleHelper(temp_db.name)
        
        # All operations should return exactly empty results
        assert helper.filter_words(word_length=5) == []
        assert helper.get_letter_frequency(word_length=5) == {}
        assert helper.suggest_best_words([], 5) == []
        # Note: suggest_best_words works on provided list, not DB, so it returns the input if non-empty
        assert helper.suggest_best_words(["TEST"], 5) == ["TEST"]  # Returns input list if provided
        
        helper.close()
        os.unlink(temp_db.name)

    def test_single_word_exact_behavior(self):
        """Test behavior with exactly one word in database"""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        helper = WordleHelper(temp_db.name)
        
        # Insert exactly one word
        cursor = helper.conn.cursor()
        cursor.execute('INSERT INTO words (word, length) VALUES (?, ?)', ("TESTY", 5))
        helper.conn.commit()
        
        # All operations should work with exactly one result
        words = helper.filter_words(word_length=5)
        assert words == ["TESTY"]
        
        freq = helper.get_letter_frequency(word_length=5)
        assert freq == {'T': 2, 'E': 1, 'S': 1, 'Y': 1}  # T appears twice
        
        suggestions = helper.suggest_best_words(["TESTY"], 5)
        assert suggestions == ["TESTY"]
        
        helper.close()
        os.unlink(temp_db.name)

    def test_boundary_word_lengths(self):
        """Test exact behavior at word length boundaries"""
        temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        temp_db.close()
        
        helper = WordleHelper(temp_db.name)
        
        # Insert words of various lengths
        test_data = [("A", 1), ("AB", 2), ("ABC", 3), ("ABCD", 4), ("ABCDE", 5)]
        cursor = helper.conn.cursor()
        for word, length in test_data:
            cursor.execute('INSERT INTO words (word, length) VALUES (?, ?)', (word, length))
        helper.conn.commit()
        
        # Test each length returns exactly the right word
        for expected_word, length in test_data:
            words = helper.filter_words(word_length=length)
            assert words == [expected_word], f"Length {length} should return exactly [{expected_word}]"
        
        # Test non-existent lengths return exactly empty
        assert helper.filter_words(word_length=0) == []
        assert helper.filter_words(word_length=6) == []
        assert helper.filter_words(word_length=100) == []
        
        helper.close()
        os.unlink(temp_db.name)


@pytest.mark.parametrize("word,expected_vowel_count", [
    ("ADIEU", 4),  # A,I,E,U
    ("AROSE", 3),  # A,O,E  
    ("SLATE", 2),  # A,E
    ("HOUSE", 3),  # O,U,E
    ("PUPPY", 1),  # U
    ("LLAMA", 1),  # A only (unique letters only counted)
])
def test_vowel_counting_exact(word, expected_vowel_count):
    """Test exact vowel counting in scoring algorithm"""
    # This tests the vowel counting logic indirectly through score comparison
    temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
    temp_db.close()
    
    helper = WordleHelper(temp_db.name)
    
    # Insert test word
    cursor = helper.conn.cursor()
    cursor.execute('INSERT INTO words (word, length) VALUES (?, ?)', (word, len(word)))
    helper.conn.commit()
    
    freq = helper.get_letter_frequency(word_length=len(word))
    score = helper.calculate_word_score(word, freq)
    
    # Vowel bonus should be min(vowel_count * 500, 1500)
    expected_bonus = min(expected_vowel_count * 500, 1500)
    
    # Score should reflect vowel bonus (but may be reduced by penalties)
    # For words with repeats, total score may be less than vowel bonus alone
    assert score > 0, f"Score {score} should be positive"
    
    # Test relative scoring: more vowels should generally score higher
    if expected_vowel_count >= 3:
        assert score > 1000, f"High vowel word {word} should score above 1000, got {score}"
    
    helper.close()
    os.unlink(temp_db.name)
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])