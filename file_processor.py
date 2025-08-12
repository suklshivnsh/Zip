import os
import zipfile
import tempfile
import shutil
import logging
import asyncio
import aiohttp
import aiofiles
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
from config import Config
from utils import (
    format_file_size, 
    is_media_file, 
    safe_filename, 
    get_file_hash,
    clean_temp_files
)
from episode_detector import EpisodeDetector, EpisodeInfo
from progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)

@dataclass
class ProcessedFile:
    """Information about a processed file."""
    original_path: str
    new_path: str
    filename: str
    new_filename: str
    size: int
    file_type: str
    episode_info: Optional[EpisodeInfo] = None
    hash: str = ""
    
@dataclass
class ProcessingResult:
    """Result of ZIP file processing."""
    success: bool
    processed_files: List[ProcessedFile]
    errors: List[str]
    total_size: int
    extraction_path: str
    
class FileProcessor:
    """Handles ZIP file extraction and processing."""
    
    def __init__(self, episode_detector: Optional[EpisodeDetector] = None):
        self.episode_detector = episode_detector or EpisodeDetector()
        self.temp_dirs: List[str] = []
        
    async def process_zip_file(self, 
                             zip_path: str, 
                             progress_tracker: Optional[ProgressTracker] = None,
                             rename_files: bool = True) -> ProcessingResult:
        """Process a ZIP file and extract/organize its contents."""
        logger.info(f"Starting to process ZIP file: {zip_path}")
        
        # Create temporary extraction directory
        extract_dir = tempfile.mkdtemp(prefix="zip_extract_", dir=Config.TEMP_DIR)
        self.temp_dirs.append(extract_dir)
        
        result = ProcessingResult(
            success=False,
            processed_files=[],
            errors=[],
            total_size=0,
            extraction_path=extract_dir
        )
        
        try:
            # Extract ZIP file
            extraction_success = await self._extract_zip(zip_path, extract_dir, result)
            if not extraction_success:
                return result
                
            # Find and process media files
            media_files = self._find_media_files(extract_dir)
            
            if not media_files:
                result.errors.append("No media files found in ZIP archive")
                return result
                
            logger.info(f"Found {len(media_files)} media files to process")
            
            # Initialize progress tracking
            if progress_tracker:
                total_size = sum(os.path.getsize(f) for f in media_files)
                progress_tracker.start(len(media_files), total_size)
                
            # Process each media file
            for file_path in media_files:
                try:
                    processed_file = await self._process_media_file(
                        file_path, extract_dir, rename_files
                    )
                    result.processed_files.append(processed_file)
                    result.total_size += processed_file.size
                    
                    # Update progress
                    if progress_tracker:
                        progress_tracker.update_file_progress(
                            processed_file.new_filename, 
                            processed_file.size, 
                            completed=True
                        )
                        
                except Exception as e:
                    error_msg = f"Error processing {os.path.basename(file_path)}: {str(e)}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
                    
            result.success = len(result.processed_files) > 0
            
            logger.info(f"ZIP processing completed: {len(result.processed_files)} files processed, "
                       f"{len(result.errors)} errors")
                       
        except Exception as e:
            error_msg = f"Fatal error processing ZIP file: {str(e)}"
            result.errors.append(error_msg)
            logger.error(error_msg)
            
        return result
        
    async def _extract_zip(self, zip_path: str, extract_dir: str, result: ProcessingResult) -> bool:
        """Extract ZIP file contents."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check for password protection
                try:
                    zip_ref.testzip()
                except RuntimeError as e:
                    if "Bad password" in str(e) or "encrypted" in str(e).lower():
                        result.errors.append("ZIP file is password protected")
                        return False
                    raise
                    
                # Get list of files to extract
                file_list = zip_ref.namelist()
                logger.info(f"ZIP contains {len(file_list)} files")
                
                # Extract files
                for file_info in zip_ref.infolist():
                    try:
                        # Skip directories
                        if file_info.is_dir():
                            continue
                            
                        # Create safe filename
                        safe_name = safe_filename(file_info.filename)
                        extract_path = os.path.join(extract_dir, safe_name)
                        
                        # Ensure directory exists
                        os.makedirs(os.path.dirname(extract_path), exist_ok=True)
                        
                        # Extract file
                        with zip_ref.open(file_info) as source, open(extract_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                            
                    except Exception as e:
                        logger.warning(f"Error extracting {file_info.filename}: {e}")
                        continue
                        
                logger.info(f"Successfully extracted ZIP to {extract_dir}")
                return True
                
        except zipfile.BadZipFile:
            result.errors.append("Invalid or corrupted ZIP file")
            return False
        except Exception as e:
            result.errors.append(f"Error extracting ZIP: {str(e)}")
            return False
            
    def _find_media_files(self, directory: str) -> List[str]:
        """Find all media files in the extracted directory."""
        media_files = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if is_media_file(file):
                    file_path = os.path.join(root, file)
                    media_files.append(file_path)
                    
        # Sort by filename for consistent processing order
        media_files.sort()
        return media_files
        
    async def _process_media_file(self, 
                                file_path: str, 
                                base_dir: str, 
                                rename_file: bool) -> ProcessedFile:
        """Process a single media file."""
        filename = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Detect file type
        file_type = "video" if filename.lower().endswith(tuple(Config.SUPPORTED_VIDEO_FORMATS)) else \
                   "audio" if filename.lower().endswith(tuple(Config.SUPPORTED_AUDIO_FORMATS)) else \
                   "subtitle"
                   
        # Generate file hash
        file_hash = get_file_hash(file_path)
        
        # Detect episode information
        episode_info = None
        new_filename = filename
        
        if rename_file and file_type in ["video", "audio"]:
            episode_info = self.episode_detector.detect_episode_info(filename)
            new_filename = self.episode_detector.generate_new_filename(episode_info)
            
        # Create new file path
        new_path = os.path.join(base_dir, new_filename)
        
        # Rename file if necessary
        if new_filename != filename:
            try:
                shutil.move(file_path, new_path)
                logger.info(f"Renamed: {filename} -> {new_filename}")
            except Exception as e:
                logger.warning(f"Error renaming {filename}: {e}")
                new_path = file_path
                new_filename = filename
                
        return ProcessedFile(
            original_path=file_path,
            new_path=new_path,
            filename=filename,
            new_filename=new_filename,
            size=file_size,
            file_type=file_type,
            episode_info=episode_info,
            hash=file_hash
        )
        
    async def download_zip_from_url(self, 
                                  url: str, 
                                  progress_callback: Optional[Callable[[int, int], None]] = None) -> Optional[str]:
        """Download ZIP file from URL."""
        try:
            # Create temporary file for download
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix='.zip', 
                dir=Config.TEMP_DIR
            )
            temp_path = temp_file.name
            temp_file.close()
            
            logger.info(f"Downloading ZIP from: {url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download ZIP: HTTP {response.status}")
                        os.remove(temp_path)
                        return None
                        
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(temp_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            await f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress
                            if progress_callback:
                                progress_callback(downloaded, total_size)
                                
            logger.info(f"Successfully downloaded ZIP: {format_file_size(downloaded)}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Error downloading ZIP from {url}: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return None
            
    def get_processing_preview(self, zip_path: str) -> Dict[str, Any]:
        """Get a preview of what would be processed without actually processing."""
        try:
            preview = {
                'valid_zip': False,
                'total_files': 0,
                'media_files': 0,
                'file_list': [],
                'estimated_size': 0,
                'errors': []
            }
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                preview['valid_zip'] = True
                file_list = zip_ref.namelist()
                preview['total_files'] = len(file_list)
                
                for file_info in zip_ref.infolist():
                    if not file_info.is_dir():
                        filename = os.path.basename(file_info.filename)
                        
                        if is_media_file(filename):
                            preview['media_files'] += 1
                            preview['estimated_size'] += file_info.file_size
                            
                            # Get episode info preview
                            episode_info = self.episode_detector.detect_episode_info(filename)
                            new_filename = self.episode_detector.generate_new_filename(episode_info)
                            
                            preview['file_list'].append({
                                'original': filename,
                                'new': new_filename,
                                'size': file_info.file_size,
                                'type': 'video' if filename.lower().endswith(tuple(Config.SUPPORTED_VIDEO_FORMATS)) else 'audio'
                            })
                            
            return preview
            
        except zipfile.BadZipFile:
            return {
                'valid_zip': False,
                'errors': ['Invalid or corrupted ZIP file']
            }
        except Exception as e:
            return {
                'valid_zip': False,
                'errors': [f'Error reading ZIP file: {str(e)}']
            }
            
    def cleanup_temp_files(self) -> None:
        """Clean up temporary extraction directories."""
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error cleaning up {temp_dir}: {e}")
                
        self.temp_dirs.clear()
        
        # Also clean up old temp files
        clean_temp_files(Config.TEMP_DIR)
        
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get detailed information about a processed file."""
        try:
            stats = os.stat(file_path)
            filename = os.path.basename(file_path)
            
            info = {
                'filename': filename,
                'size': stats.st_size,
                'size_formatted': format_file_size(stats.st_size),
                'modified': stats.st_mtime,
                'is_media': is_media_file(filename),
                'file_type': 'unknown'
            }
            
            if filename.lower().endswith(tuple(Config.SUPPORTED_VIDEO_FORMATS)):
                info['file_type'] = 'video'
            elif filename.lower().endswith(tuple(Config.SUPPORTED_AUDIO_FORMATS)):
                info['file_type'] = 'audio'
            elif filename.lower().endswith(tuple(Config.SUPPORTED_SUBTITLE_FORMATS)):
                info['file_type'] = 'subtitle'
                
            # Get episode info if it's a media file
            if info['is_media']:
                episode_info = self.episode_detector.detect_episode_info(filename)
                info['episode_info'] = {
                    'season': episode_info.season,
                    'episode': episode_info.episode,
                    'show_name': episode_info.show_name,
                    'quality': episode_info.quality,
                    'audio': episode_info.audio
                }
                
            return info
            
        except Exception as e:
            logger.error(f"Error getting file info for {file_path}: {e}")
            return {'error': str(e)}
            
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup_temp_files()