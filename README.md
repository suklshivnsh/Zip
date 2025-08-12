# Telegram ZIP Bot

A powerful Telegram bot that can extract ZIP files, detect episodes, rename files with custom templates, and upload them with progress tracking.

## Features

### 🔧 Core Functionality
- **ZIP File Extraction**: Extract and process ZIP files from direct uploads or download links
- **Smart Episode Detection**: Automatically detect season/episode numbers from various filename formats
- **Custom File Renaming**: Use templates to rename files with episode info, quality, audio, etc.
- **Custom Thumbnails**: Set custom thumbnails for uploads via `/t` command
- **Progress Tracking**: Real-time progress bars with ETA updates every 5 seconds
- **Dump Channel Support**: Upload files to specified channels
- **Modular Structure**: Well-organized code for easy maintenance

### 📺 Episode Detection Formats
- `S01E01`, `Season 1 Episode 1`
- `1x01`, `E01`, `Episode 1`
- `- 01`, `_01_`, `.01.`
- And many more patterns

### 🎯 File Renaming Templates
Default template: `[S{Season} - E{Episode}] {ShowName} [{Quality}] [{Audio}] @{Channel}.{Extension}`

Available variables:
- `{Season}` - Season number (01, 02, etc.)
- `{Episode}` - Episode number (01, 02, etc.)
- `{ShowName}` - Detected show name
- `{Quality}` - Video quality (720p, 1080p, etc.)
- `{Audio}` - Audio format (AAC, AC3, etc.)
- `{Channel}` - Your channel name
- `{Extension}` - File extension

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/suklshivnsh/Zip.git
   cd Zip
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your bot token and settings
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_USER_ID=your_telegram_user_id_here

# Optional
DUMP_CHANNEL_ID=default_dump_channel_id
MAX_FILE_SIZE_MB=2000
TEMP_DIR=./temp
THUMBNAILS_DIR=./thumbnails
PROGRESS_UPDATE_INTERVAL=5
STATUS_UPDATE_FILES=4
DEFAULT_RENAME_TEMPLATE=[S{Season} - E{Episode}] {ShowName} [{Quality}] [{Audio}] @{Channel}.{Extension}
```

## Usage

### Basic Commands

- `/start` - Welcome message and feature overview
- `/help` - Detailed help and command list
- `/settings` - View current user settings

### File Processing

1. **Send ZIP file directly** - Upload a ZIP file to the bot
2. **Send download link** - Send a direct URL to a ZIP file
3. **Bot will automatically**:
   - Extract the ZIP contents
   - Detect episodes and show information
   - Rename files according to your template
   - Upload with progress tracking

### Customization Commands

- `/e <template>` - Set custom rename template
- `/t` - Set custom thumbnail (reply to image)
- `/channel <name>` - Set channel name for @mentions
- `/dump <chat_id>` - Set dump channel for uploads
- `/preview` - Preview how files will be renamed

### Example Usage

```
# Set channel name
/channel MyAwesomeChannel

# Set custom rename template
/e [{Quality}] {ShowName} - S{Season}E{Episode} @{Channel}.{Extension}

# Set custom thumbnail
/t (reply to an image)

# Set dump channel
/dump -1001234567890

# Then just send a ZIP file or URL!
```

## Supported Formats

### Video Files
`.mp4`, `.mkv`, `.avi`, `.mov`, `.wmv`, `.flv`, `.webm`, `.m4v`

### Audio Files
`.mp3`, `.flac`, `.wav`, `.aac`, `.m4a`, `.ogg`

### Subtitle Files
`.srt`, `.ass`, `.vtt`, `.sub`

## Progress Features

- 📊 Real-time progress bars
- ⏱️ ETA calculations with speed monitoring
- 🔄 Updates every 5 seconds during uploads
- 📈 Status updates after every 4 processed files
- 📝 Final summary with statistics

## File Structure

```
Zip/
├── bot.py                 # Main bot application
├── config.py              # Configuration and constants
├── file_processor.py      # ZIP extraction and processing
├── episode_detector.py    # Episode detection and renaming
├── thumbnail_handler.py   # Custom thumbnail management
├── progress_tracker.py    # Progress tracking with ETA
├── utils.py               # Utility functions
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## Requirements

- Python 3.8+
- python-telegram-bot
- aiohttp, aiofiles
- Pillow (for thumbnail processing)
- Other dependencies in requirements.txt

## License

This project is open source. Feel free to contribute!

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and feature requests, please use GitHub Issues or contact the developer.