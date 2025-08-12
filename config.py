import os
from typing import Optional

class Config:
    """Configuration class for the Telegram Bot"""
    
    # Telegram Bot Configuration
    API_ID: int = int(os.environ.get("API_ID", "0"))
    API_HASH: str = os.environ.get("API_HASH", "")
    BOT_TOKEN: str = os.environ.get("BOT_TOKEN", "")
    
    # Download Configuration
    DOWNLOAD_PATH: str = os.environ.get("DOWNLOAD_PATH", "./downloads")
    EXTRACT_PATH: str = os.environ.get("EXTRACT_PATH", "./extracted")
    
    # FFmpeg Configuration
    FFMPEG_PATH: str = os.environ.get("FFMPEG_PATH", "ffmpeg")
    
    # Bot Settings
    MAX_FILE_SIZE: int = int(os.environ.get("MAX_FILE_SIZE", "2000000000"))  # 2GB
    CHUNK_SIZE: int = int(os.environ.get("CHUNK_SIZE", "1024"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration"""
        if not cls.API_ID or not cls.API_HASH or not cls.BOT_TOKEN:
            return False
        return True