# 🎯 Wordle Helper

[![Latest Release](https://img.shields.io/github/v/release/rkreitschmann/WordleHelper)](https://github.com/rkreitschmann/WordleHelper/releases/latest)
[![Download](https://img.shields.io/github/downloads/rkreitschmann/WordleHelper/total)](https://github.com/rkreitschmann/WordleHelper/releases/latest)

An interactive Python tool to help solve Wordle puzzles by filtering words based on your clues.

## ✨ Features

- Interactive command-line interface
- Support for different word lengths
- Persistent constraints across rounds
- Max coverage guess mode
- Word frequency-based scoring
- Batch entry for multiple constraints

## 🚀 Quick Start

### Option 1: Download Executable (Recommended)
**[📥 Download Latest Release](https://github.com/rkreitschmann/WordleHelper/releases/latest)**

1. Click the link above to go to the latest release
2. Download `WordleHelper.exe` from the Assets section
3. Run the executable (no installation needed!)
4. Follow the interactive prompts

### Option 2: Run from Source
1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the script:
   ```bash
   python Wordle_helper.py
   ```

## 📋 Requirements

- Python 3.7+ (for source code)
- Windows 10+ (for executable)

## 📊 Data

The tool uses a word dictionary for suggestions. You can:
- Use the included fallback word list
- Provide your own `words_dictionary_filtered.json` file

## 🎮 How to Use

1. **Green Letters**: Enter known letters and positions (e.g., `A1 E3`)
2. **Yellow Letters**: Enter letters in wrong positions (e.g., `T2 R4`)
3. **Gray Letters**: Enter letters not in the word (e.g., `QWERTY`)
4. Get filtered word suggestions with scores

## 🛠️ Building from Source

To create your own executable:

```bash
pip install pyinstaller
pyinstaller --onefile --console Wordle_helper.py
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

If you encounter issues, please [open an issue](../../issues).