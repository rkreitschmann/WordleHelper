import json
import re

def filter_valid_english_words(input_file, output_file):
	"""
	Filter words_dictionary.json to contain only valid English words
	"""
	try:
		# Read the input JSON file
		with open(input_file, 'r', encoding='utf-8') as f:
			words_dict = json.load(f)

		# Filter for valid English words
		valid_words = {}
		deleted_words = []

		for word, value in words_dict.items():
			# Check if word contains only English letters
			if (word.isalpha() and 
				word.islower() and 
				re.match(r'^[a-z]+$', word) and
				len(word) >= 2):  # minimum 2 characters
				valid_words[word] = value
			else:
				deleted_words.append(word)

		# Write filtered words to output file
		with open(output_file, 'w', encoding='utf-8') as f:
			json.dump(valid_words, f, indent=2, ensure_ascii=False)

		# Write deleted words to a separate file
		deleted_file = 'deleted_words.txt'
		with open(deleted_file, 'w', encoding='utf-8') as f:
			for word in deleted_words:
				f.write(word + '\n')

		print(f"Filtered {len(valid_words)} valid English words from {len(words_dict)} total words")
		print(f"Output saved to: {output_file}")
		print(f"Deleted words saved to: {deleted_file}")

	except FileNotFoundError:
		print(f"Error: Could not find {input_file}")
	except json.JSONDecodeError:
		print(f"Error: Invalid JSON format in {input_file}")
	except Exception as e:
		print(f"Error: {e}")

# Usage
if __name__ == "__main__":
	input_file = "words_dictionary.json"
	output_file = "valid_english_words.json"
	filter_valid_english_words(input_file, output_file)