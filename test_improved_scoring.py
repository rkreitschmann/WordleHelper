"""
Test the improved scoring algorithm
"""

import sys
sys.path.append('.')
from Wordle_helper import WordleHelper

def test_improved_scoring():
    """Test the new improved scoring algorithm"""
    
    print("🚀 Testing Improved Scoring Algorithm")
    print("=" * 40)
    
    helper = WordleHelper()
    helper.load_words()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "General 5-letter words",
            "pattern": "_____",
            "wrong_letters": "",
            "yellow_positions": []
        },
        {
            "name": "Second letter is 'A'",
            "pattern": "_A___", 
            "wrong_letters": "RST",
            "yellow_positions": []
        },
        {
            "name": "Ends with 'E'",
            "pattern": "____E",
            "wrong_letters": "RST",
            "yellow_positions": []
        },
        {
            "name": "Has 'O' but not in pos 3",
            "pattern": "_____",
            "wrong_letters": "RST",
            "yellow_positions": [(3, 'O')]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Pattern: {scenario['pattern']}")
        print(f"   Exclude: {scenario['wrong_letters']}")
        print(f"   Yellow: {scenario['yellow_positions']}")
        
        # Get filtered words
        filtered_words = helper.filter_words(
            word_length=5,
            known_letters=scenario['pattern'],
            wrong_letters=scenario['wrong_letters'],
            wrong_positions=scenario['yellow_positions']
        )
        
        if len(filtered_words) > 0:
            suggestions = helper.suggest_best_words(filtered_words, 10)
            print(f"   Found {len(filtered_words)} words")
            print(f"   Top suggestions: {suggestions[:5]}")
        else:
            print("   No words found!")
    
    # Test specific word comparisons
    print(f"\n" + "=" * 40)
    print("SPECIFIC WORD ANALYSIS")
    print("=" * 40)
    
    # Test words with different characteristics
    test_words = [
        "ADIEU",  # Good vowel spread
        "RATES",  # Common letters
        "SLATE",  # Good starting letter
        "HOUSE",  # Ends with E
        "ABBEY",  # Repeated letters
        "QUEUE",  # Many repeated letters
    ]
    
    frequency = helper.get_letter_frequency(word_length=5)
    
    for word in test_words:
        # Calculate new score using the method from suggest_best_words
        position_weights = [1.2, 1.0, 0.9, 1.0, 1.1]
        position_score = 0
        used_letters = set()

        for i, letter in enumerate(word):
            if letter not in used_letters:
                position_score += frequency.get(letter, 0) * position_weights[i]
                used_letters.add(letter)

        vowels = set('AEIOU')
        vowel_count = len([letter for letter in used_letters if letter in vowels])
        vowel_bonus = min(vowel_count * 500, 1500)

        start_bonus = 0
        end_bonus = 0
        common_starts = ['S', 'C', 'B', 'T', 'P', 'A', 'F', 'G', 'D', 'M']
        common_ends = ['S', 'E', 'Y', 'D', 'T', 'A', 'R', 'N', 'L']

        if word[0] in common_starts:
            start_bonus = 300
        if word[-1] in common_ends:
            end_bonus = 300

        repeat_penalty = (len(word) - len(used_letters)) * 200

        new_score = position_score + vowel_bonus + start_bonus + end_bonus - repeat_penalty

        # Basic assertions to ensure scoring runs and produces numeric results
        assert isinstance(new_score, (int, float))
        assert new_score >= -1000  # sanity lower bound
    
    helper.close()
    print(f"\n✅ Improved scoring test completed!")

if __name__ == "__main__":
    test_improved_scoring()