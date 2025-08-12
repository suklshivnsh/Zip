import os
import hashlib
import logging
from typing import Optional, Dict, Any
from PIL import Image
from config import Config
from utils import safe_filename, get_file_hash

logger = logging.getLogger(__name__)

class ThumbnailHandler:
    """Handles custom thumbnail management for the bot."""
    
    def __init__(self):
        self.user_thumbnails: Dict[int, str] = {}  # user_id -> thumbnail_path
        self.default_thumbnail: Optional[str] = None
        
    def set_user_thumbnail(self, user_id: int, thumbnail_path: str) -> bool:
        """Set custom thumbnail for a user."""
        try:
            if os.path.exists(thumbnail_path):
                # Validate image
                if self._validate_thumbnail(thumbnail_path):
                    self.user_thumbnails[user_id] = thumbnail_path
                    logger.info(f"Set custom thumbnail for user {user_id}: {thumbnail_path}")
                    return True
                else:
                    logger.error(f"Invalid thumbnail format: {thumbnail_path}")
                    return False
            else:
                logger.error(f"Thumbnail file not found: {thumbnail_path}")
                return False
        except Exception as e:
            logger.error(f"Error setting thumbnail for user {user_id}: {e}")
            return False
            
    def get_user_thumbnail(self, user_id: int) -> Optional[str]:
        """Get custom thumbnail for a user."""
        return self.user_thumbnails.get(user_id, self.default_thumbnail)
        
    def remove_user_thumbnail(self, user_id: int) -> bool:
        """Remove custom thumbnail for a user."""
        if user_id in self.user_thumbnails:
            old_path = self.user_thumbnails[user_id]
            del self.user_thumbnails[user_id]
            
            # Clean up the file if no other users are using it
            if old_path not in self.user_thumbnails.values():
                try:
                    os.remove(old_path)
                    logger.info(f"Removed thumbnail file: {old_path}")
                except Exception as e:
                    logger.error(f"Error removing thumbnail file {old_path}: {e}")
                    
            logger.info(f"Removed custom thumbnail for user {user_id}")
            return True
        return False
        
    def save_thumbnail_from_telegram(self, user_id: int, file_path: str, file_data: bytes) -> bool:
        """Save thumbnail from Telegram file upload."""
        try:
            # Generate unique filename
            file_hash = hashlib.md5(file_data).hexdigest()[:8]
            filename = f"thumb_{user_id}_{file_hash}.jpg"
            save_path = os.path.join(Config.THUMBNAILS_DIR, filename)
            
            # Save the file
            with open(save_path, 'wb') as f:
                f.write(file_data)
                
            # Validate and process the image
            if self._validate_and_process_thumbnail(save_path):
                # Remove old thumbnail if exists
                if user_id in self.user_thumbnails:
                    old_path = self.user_thumbnails[user_id]
                    if old_path != save_path and os.path.exists(old_path):
                        os.remove(old_path)
                        
                self.user_thumbnails[user_id] = save_path
                logger.info(f"Saved and set new thumbnail for user {user_id}: {save_path}")
                return True
            else:
                # Remove invalid file
                if os.path.exists(save_path):
                    os.remove(save_path)
                return False
                
        except Exception as e:
            logger.error(f"Error saving thumbnail for user {user_id}: {e}")
            return False
            
    def _validate_thumbnail(self, image_path: str) -> bool:
        """Validate thumbnail image format and size."""
        try:
            with Image.open(image_path) as img:
                # Check format
                if img.format not in ['JPEG', 'PNG', 'WEBP']:
                    logger.error(f"Unsupported image format: {img.format}")
                    return False
                    
                # Check size (should be reasonable for thumbnail)
                width, height = img.size
                if width > 1920 or height > 1920:
                    logger.warning(f"Large thumbnail size: {width}x{height}")
                    
                if width < 50 or height < 50:
                    logger.error(f"Thumbnail too small: {width}x{height}")
                    return False
                    
                return True
                
        except Exception as e:
            logger.error(f"Error validating thumbnail {image_path}: {e}")
            return False
            
    def _validate_and_process_thumbnail(self, image_path: str) -> bool:
        """Validate and process thumbnail (resize if needed)."""
        try:
            with Image.open(image_path) as img:
                # Validate format
                if img.format not in ['JPEG', 'PNG', 'WEBP']:
                    return False
                    
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                    
                # Resize if too large (max 1280x720 for reasonable size)
                max_width, max_height = 1280, 720
                if img.width > max_width or img.height > max_height:
                    # Calculate new size maintaining aspect ratio
                    ratio = min(max_width / img.width, max_height / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.info(f"Resized thumbnail to {new_width}x{new_height}")
                    
                # Save processed image
                img.save(image_path, 'JPEG', quality=85, optimize=True)
                return True
                
        except Exception as e:
            logger.error(f"Error processing thumbnail {image_path}: {e}")
            return False
            
    def generate_thumbnail_from_video(self, video_path: str, output_path: str, timestamp: float = 30.0) -> bool:
        """Generate thumbnail from video file (requires ffmpeg)."""
        try:
            import subprocess
            
            # Check if ffmpeg is available
            try:
                subprocess.run(['ffmpeg', '-version'], 
                             capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("ffmpeg not available, cannot generate video thumbnail")
                return False
                
            # Generate thumbnail using ffmpeg
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-ss', str(timestamp),
                '-vframes', '1',
                '-q:v', '2',
                '-y',  # Overwrite output file
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(output_path):
                # Validate and process the generated thumbnail
                if self._validate_and_process_thumbnail(output_path):
                    logger.info(f"Generated video thumbnail: {output_path}")
                    return True
                else:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    return False
            else:
                logger.error(f"ffmpeg failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating video thumbnail: {e}")
            return False
            
    def create_default_thumbnail(self, text: str = "ZIP Bot") -> str:
        """Create a default thumbnail with text."""
        try:
            # Create a simple thumbnail with text
            img = Image.new('RGB', (320, 180), color='#2c3e50')
            
            # Try to add text if PIL supports it
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                # Try to use a font, fallback to default
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
                except:
                    font = ImageFont.load_default()
                    
                # Center the text
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (320 - text_width) // 2
                y = (180 - text_height) // 2
                
                draw.text((x, y), text, fill='white', font=font)
                
            except ImportError:
                # PIL doesn't have text support
                pass
                
            # Save default thumbnail
            default_path = os.path.join(Config.THUMBNAILS_DIR, 'default.jpg')
            img.save(default_path, 'JPEG', quality=85)
            
            self.default_thumbnail = default_path
            logger.info(f"Created default thumbnail: {default_path}")
            return default_path
            
        except Exception as e:
            logger.error(f"Error creating default thumbnail: {e}")
            return ""
            
    def get_thumbnail_info(self, user_id: int) -> Dict[str, Any]:
        """Get thumbnail information for a user."""
        thumbnail_path = self.get_user_thumbnail(user_id)
        
        if not thumbnail_path or not os.path.exists(thumbnail_path):
            return {
                'has_thumbnail': False,
                'path': None,
                'size': None,
                'dimensions': None
            }
            
        try:
            file_size = os.path.getsize(thumbnail_path)
            
            with Image.open(thumbnail_path) as img:
                dimensions = img.size
                
            return {
                'has_thumbnail': True,
                'path': thumbnail_path,
                'size': file_size,
                'dimensions': dimensions
            }
            
        except Exception as e:
            logger.error(f"Error getting thumbnail info: {e}")
            return {
                'has_thumbnail': False,
                'path': None,
                'size': None,
                'dimensions': None
            }
            
    def cleanup_unused_thumbnails(self) -> int:
        """Clean up unused thumbnail files."""
        try:
            cleaned = 0
            used_thumbnails = set(self.user_thumbnails.values())
            if self.default_thumbnail:
                used_thumbnails.add(self.default_thumbnail)
                
            for filename in os.listdir(Config.THUMBNAILS_DIR):
                file_path = os.path.join(Config.THUMBNAILS_DIR, filename)
                if os.path.isfile(file_path) and file_path not in used_thumbnails:
                    os.remove(file_path)
                    cleaned += 1
                    logger.info(f"Cleaned up unused thumbnail: {file_path}")
                    
            return cleaned
            
        except Exception as e:
            logger.error(f"Error during thumbnail cleanup: {e}")
            return 0