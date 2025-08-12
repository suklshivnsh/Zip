import os
import hashlib
import shutil
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

def get_file_hash(file_path: str) -> str:
    """Generate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error generating hash for {file_path}: {e}")
        return ""

def format_file_size(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_duration(seconds: int) -> str:
    """Convert seconds to human readable duration."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def safe_filename(filename: str) -> str:
    """Create a safe filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename.strip()

def clean_temp_files(temp_dir: str, max_age_hours: int = 24) -> None:
    """Clean up temporary files older than specified hours."""
    try:
        current_time = datetime.now()
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    age_hours = (current_time - file_time).total_seconds() / 3600
                    
                    if age_hours > max_age_hours:
                        os.remove(file_path)
                        logger.info(f"Cleaned up old temp file: {file_path}")
                except Exception as e:
                    logger.error(f"Error cleaning temp file {file_path}: {e}")
                    
            # Remove empty directories
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):
                        os.rmdir(dir_path)
                        logger.info(f"Removed empty temp directory: {dir_path}")
                except Exception as e:
                    logger.error(f"Error removing temp directory {dir_path}: {e}")
                    
    except Exception as e:
        logger.error(f"Error during temp cleanup: {e}")

def is_video_file(filename: str) -> bool:
    """Check if file is a video file based on extension."""
    from config import Config
    return any(filename.lower().endswith(ext) for ext in Config.SUPPORTED_VIDEO_FORMATS)

def is_audio_file(filename: str) -> bool:
    """Check if file is an audio file based on extension."""
    from config import Config
    return any(filename.lower().endswith(ext) for ext in Config.SUPPORTED_AUDIO_FORMATS)

def is_subtitle_file(filename: str) -> bool:
    """Check if file is a subtitle file based on extension.""" 
    from config import Config
    return any(filename.lower().endswith(ext) for ext in Config.SUPPORTED_SUBTITLE_FORMATS)

def is_media_file(filename: str) -> bool:
    """Check if file is any type of media file."""
    return is_video_file(filename) or is_audio_file(filename) or is_subtitle_file(filename)

def create_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Create a visual progress bar."""
    if total == 0:
        return "█" * width
    
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    percentage = (current / total) * 100
    
    return f"[{bar}] {percentage:.1f}%"

def escape_markdown(text: str) -> str:
    """Escape markdown special characters."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def split_message(text: str, max_length: int = 4096) -> List[str]:
    """Split long messages into chunks that fit Telegram's message limit."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split('\n'):
        if len(current_chunk) + len(line) + 1 <= max_length:
            current_chunk += line + '\n'
        else:
            if current_chunk:
                chunks.append(current_chunk.rstrip())
            current_chunk = line + '\n'
    
    if current_chunk:
        chunks.append(current_chunk.rstrip())
    
    return chunks

def get_file_extension(filename: str) -> str:
    """Get file extension from filename."""
    return os.path.splitext(filename)[1].lower()

def get_file_name_without_extension(filename: str) -> str:
    """Get filename without extension."""
    return os.path.splitext(filename)[0]