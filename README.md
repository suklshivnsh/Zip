# Zip Extraction Telegram Bot

A Telegram bot using Pyrogram that can extract zip files and rename them with automatic episode detection.

## Features

- 📦 **Zip File Extraction**: Accepts zip files sent directly or via external links
- 🎯 **Episode Detection**: Automatically detects episode numbers from filenames
- 🏷️ **Smart Renaming**: Rename extracted files using custom patterns with `{Episode}` placeholder
- ⚡ **Fast Processing**: Efficient file handling with async operations
- 🔗 **External Links**: Download and process zip files from external URLs
- 📱 **User-Friendly**: Simple commands and clear status messages

## Commands

- `/start` - Welcome message and bot introduction
- `/help` - Detailed help and usage instructions
- `/e <filename_pattern>` - Set filename pattern for extraction and renaming

### Example Usage

```
/e Suspicious Maid [S1 - E{Episode}] [480p] [MultiAudio] @Animejunctions2.mkv
```

Then send a zip file, and the bot will:
1. Extract the zip file
2. Detect episode numbers from the extracted filenames
3. Rename files according to your pattern (replacing `{Episode}` with detected numbers)
4. Send back the processed files

## Installation

1. Clone this repository:
```bash
git clone https://github.com/suklshivnsh/Zip.git
cd Zip
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up configuration:
```bash
cp .env.example .env
# Edit .env with your bot credentials
```

4. Create a Telegram Bot:
   - Message [@BotFather](https://t.me/BotFather) on Telegram
   - Create a new bot with `/newbot`
   - Get your bot token
   - Get your API ID and API Hash from [my.telegram.org](https://my.telegram.org)

5. Configure the bot:
   - Edit `.env` file with your credentials:
     ```
     API_ID=your_api_id
     API_HASH=your_api_hash
     BOT_TOKEN=your_bot_token
     ```

6. Run the bot:
```bash
python main.py
```

## Configuration

The bot can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_ID` | Telegram API ID | Required |
| `API_HASH` | Telegram API Hash | Required |
| `BOT_TOKEN` | Telegram Bot Token | Required |
| `DOWNLOAD_PATH` | Path for downloading files | `./downloads` |
| `EXTRACT_PATH` | Path for extracted files | `./extracted` |
| `MAX_FILE_SIZE` | Maximum file size in bytes | `2000000000` (2GB) |
| `CHUNK_SIZE` | Download chunk size | `1024` |

## Episode Detection

The bot can automatically detect episode numbers from various filename formats:

- `E01`, `e01` - Standard episode format
- `Episode 01` - Full word format  
- `S01E01` - Season and episode format
- `[01]` - Bracketed numbers
- `- 01` - Dash separated numbers
- Standalone numbers in filenames

## File Support

- **Input**: ZIP files (`.zip` format)
- **Output**: Any files contained within the zip archives
- **Size Limit**: Configurable (default 2GB)
- **Links**: Direct HTTP/HTTPS links to zip files

## Dependencies

- `pyrogram` - Telegram Bot API framework
- `tgcrypto` - Cryptographic library for Pyrogram
- `aiohttp` - Async HTTP client for downloading files
- `aiofiles` - Async file operations
- `ffmpeg-python` - FFmpeg integration (for future enhancements)
- `python-magic` - File type detection
- `requests` - HTTP library

## License

This project is open source and available under the MIT License.