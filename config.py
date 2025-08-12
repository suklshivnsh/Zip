import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
    
    # Channel Configuration
    DUMP_CHANNEL_ID = os.getenv('DUMP_CHANNEL_ID')
    
    # File Processing Settings
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 2000))
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    TEMP_DIR = os.getenv('TEMP_DIR', './temp')
    THUMBNAILS_DIR = os.getenv('THUMBNAILS_DIR', './thumbnails')
    
    # Progress Settings
    PROGRESS_UPDATE_INTERVAL = int(os.getenv('PROGRESS_UPDATE_INTERVAL', 5))
    STATUS_UPDATE_FILES = int(os.getenv('STATUS_UPDATE_FILES', 4))
    
    # Default Templates
    DEFAULT_RENAME_TEMPLATE = os.getenv(
        'DEFAULT_RENAME_TEMPLATE',
        '[S{Season} - E{Episode}] {ShowName} [{Quality}] [{Audio}] @{Channel}.{Extension}'
    )
    
    # Supported Video Formats
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'}
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.flac', '.wav', '.aac', '.m4a', '.ogg'}
    SUPPORTED_SUBTITLE_FORMATS = {'.srt', '.ass', '.vtt', '.sub'}
    
    # Episode Detection Patterns
    EPISODE_PATTERNS = [
        r'[Ss](\d+)[Ee](\d+)',  # S01E01
        r'[Ss]eason\s*(\d+)\s*[Ee]pisode\s*(\d+)',  # Season 1 Episode 1
        r'(\d+)x(\d+)',  # 1x01
        r'[Ee](\d+)',  # E01
        r'[Ee]pisode\s*(\d+)',  # Episode 1
        r'- (\d+)',  # - 01
        r'_(\d+)_',  # _01_
        r'\.(\d+)\.',  # .01.
    ]
    
    # Quality Detection Patterns
    QUALITY_PATTERNS = [
        r'(720p|1080p|1440p|2160p|4K|8K)',
        r'(HD|FHD|UHD|SD)',
        r'(WEB-DL|BluRay|BRRip|DVDRip|HDTV|WEBRip)',
    ]
    
    # Audio Detection Patterns  
    AUDIO_PATTERNS = [
        r'(AAC|AC3|DTS|FLAC|MP3|OGG|PCM|TrueHD|Atmos)',
        r'(2\.0|5\.1|7\.1)',
        r'(Stereo|Mono)',
    ]

# Ensure directories exist
os.makedirs(Config.TEMP_DIR, exist_ok=True)
os.makedirs(Config.THUMBNAILS_DIR, exist_ok=True)