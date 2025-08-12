import re
import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from config import Config
from utils import get_file_name_without_extension, get_file_extension

logger = logging.getLogger(__name__)

@dataclass
class EpisodeInfo:
    """Container for episode information."""
    season: Optional[int] = None
    episode: Optional[int] = None
    show_name: str = ""
    quality: str = ""
    audio: str = ""
    original_filename: str = ""
    extension: str = ""
    
class EpisodeDetector:
    """Detects episode information from filenames and handles renaming."""
    
    def __init__(self):
        self.rename_template = Config.DEFAULT_RENAME_TEMPLATE
        self.custom_channel = ""
        
    def set_rename_template(self, template: str) -> None:
        """Set custom rename template."""
        self.rename_template = template
        logger.info(f"Rename template set to: {template}")
        
    def set_channel(self, channel: str) -> None:
        """Set custom channel name for renaming."""
        self.custom_channel = channel
        logger.info(f"Channel set to: {channel}")
        
    def detect_episode_info(self, filename: str) -> EpisodeInfo:
        """Extract episode information from filename."""
        info = EpisodeInfo()
        info.original_filename = filename
        info.extension = get_file_extension(filename)
        
        # Clean filename for analysis
        clean_name = get_file_name_without_extension(filename)
        
        # Try to extract episode and season information
        season, episode = self._extract_episode_season(clean_name)
        info.season = season
        info.episode = episode
        
        # Extract show name
        info.show_name = self._extract_show_name(clean_name)
        
        # Extract quality information
        info.quality = self._extract_quality(clean_name)
        
        # Extract audio information
        info.audio = self._extract_audio(clean_name)
        
        logger.info(f"Detected info for '{filename}': S{info.season}E{info.episode}, "
                   f"Show: {info.show_name}, Quality: {info.quality}, Audio: {info.audio}")
        
        return info
        
    def _extract_episode_season(self, filename: str) -> tuple[Optional[int], Optional[int]]:
        """Extract season and episode numbers from filename."""
        for pattern in Config.EPISODE_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) == 2:
                    # Season and Episode
                    try:
                        season = int(groups[0])
                        episode = int(groups[1])
                        return season, episode
                    except ValueError:
                        continue
                elif len(groups) == 1:
                    # Episode only
                    try:
                        episode = int(groups[0])
                        return 1, episode  # Default to season 1
                    except ValueError:
                        continue
        
        # If no pattern matches, try to find any number sequence
        numbers = re.findall(r'\d+', filename)
        if numbers:
            try:
                # Use the last number as episode
                episode = int(numbers[-1])
                return 1, episode
            except ValueError:
                pass
                
        return None, None
        
    def _extract_show_name(self, filename: str) -> str:
        """Extract show name from filename."""
        # Remove common separators and clean up
        name = filename
        
        # Remove episode patterns
        for pattern in Config.EPISODE_PATTERNS:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
            
        # Remove quality patterns
        for pattern in Config.QUALITY_PATTERNS:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
            
        # Remove audio patterns
        for pattern in Config.AUDIO_PATTERNS:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)
            
        # Clean up separators and extra spaces
        name = re.sub(r'[._\-\[\]()]', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common release group indicators
        name = re.sub(r'\b(x264|x265|h264|h265|hevc|avc)\b', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\b(web-dl|webrip|bluray|brrip|dvdrip|hdtv|hdcam)\b', '', name, flags=re.IGNORECASE)
        
        # Final cleanup
        name = re.sub(r'\s+', ' ', name).strip()
        
        # If name is too short or empty, use original filename
        if len(name) < 2:
            name = get_file_name_without_extension(filename)
            
        return name.title()
        
    def _extract_quality(self, filename: str) -> str:
        """Extract quality information from filename."""
        for pattern in Config.QUALITY_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Check for resolution in filename
        if re.search(r'720', filename):
            return "720p"
        elif re.search(r'1080', filename):
            return "1080p"
        elif re.search(r'2160|4K', filename, re.IGNORECASE):
            return "4K"
            
        return "Unknown"
        
    def _extract_audio(self, filename: str) -> str:
        """Extract audio information from filename."""
        for pattern in Config.AUDIO_PATTERNS:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return match.group(1).upper()
                
        return "Unknown"
        
    def generate_new_filename(self, episode_info: EpisodeInfo, custom_template: Optional[str] = None) -> str:
        """Generate new filename based on template and episode info."""
        template = custom_template or self.rename_template
        
        # Prepare replacement values
        replacements = {
            'Season': str(episode_info.season or 1).zfill(2),
            'Episode': str(episode_info.episode or 1).zfill(2),
            'ShowName': episode_info.show_name or "Unknown Show",
            'Quality': episode_info.quality or "Unknown",
            'Audio': episode_info.audio or "Unknown", 
            'Channel': self.custom_channel or "Unknown",
            'Extension': episode_info.extension or ".mkv"
        }
        
        # Remove extension from template if it's already there
        if template.endswith('.{Extension}'):
            template = template[:-12]  # Remove .{Extension}
            
        # Replace placeholders
        new_filename = template
        for key, value in replacements.items():
            new_filename = new_filename.replace(f'{{{key}}}', value)
            
        # Add extension
        new_filename += replacements['Extension']
        
        # Clean up any invalid characters
        from utils import safe_filename
        new_filename = safe_filename(new_filename)
        
        logger.info(f"Generated new filename: {new_filename}")
        return new_filename
        
    def get_batch_rename_preview(self, filenames: List[str], template: Optional[str] = None) -> List[Dict[str, str]]:
        """Generate a preview of how files would be renamed."""
        preview = []
        
        for filename in filenames:
            episode_info = self.detect_episode_info(filename)
            new_filename = self.generate_new_filename(episode_info, template)
            
            preview.append({
                'original': filename,
                'new': new_filename,
                'season': episode_info.season,
                'episode': episode_info.episode,
                'show': episode_info.show_name
            })
            
        return preview