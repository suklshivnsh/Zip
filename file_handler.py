import os
import re
import zipfile
import aiofiles
import aiohttp
import asyncio
import magic
from pathlib import Path
from typing import Optional, List, Tuple
from urllib.parse import urlparse

class FileHandler:
    """Handle file operations including download, extraction, and renaming"""
    
    def __init__(self, download_path: str, extract_path: str):
        self.download_path = Path(download_path)
        self.extract_path = Path(extract_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.extract_path.mkdir(parents=True, exist_ok=True)
    
    async def download_file(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """Download file from URL"""
        try:
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path) or "downloaded_file"
            
            file_path = self.download_path / filename
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        return str(file_path)
            return None
        except Exception as e:
            print(f"Error downloading file: {e}")
            return None
    
    def is_zip_file(self, file_path: str) -> bool:
        """Check if file is a zip file"""
        try:
            if zipfile.is_zipfile(file_path):
                return True
            # Also check using magic
            file_type = magic.from_file(file_path, mime=True)
            return file_type in ['application/zip', 'application/x-zip-compressed']
        except:
            return False
    
    def extract_zip(self, zip_path: str) -> List[str]:
        """Extract zip file and return list of extracted files"""
        extracted_files = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.extract_path)
                extracted_files = [str(self.extract_path / name) for name in zip_ref.namelist()]
            return extracted_files
        except Exception as e:
            print(f"Error extracting zip: {e}")
            return []
    
    def detect_episode_number(self, filename: str) -> Optional[int]:
        """Detect episode number from filename"""
        patterns = [
            r'[Ee](\d+)',  # E01, e01
            r'[Ee]pisode\s*(\d+)',  # Episode 01
            r'[Ss]\d+[Ee](\d+)',  # S01E01
            r'(?:^|\s)(\d+)(?:\s|$)',  # Standalone numbers
            r'\[(\d+)\]',  # [01]
            r'-\s*(\d+)',  # - 01
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return int(match.group(1))
        
        return None
    
    def rename_with_episode(self, file_path: str, new_name_pattern: str, episode_num: Optional[int] = None) -> Optional[str]:
        """Rename file according to pattern, replacing {Episode} with detected or provided episode number"""
        try:
            original_path = Path(file_path)
            
            if episode_num is None:
                episode_num = self.detect_episode_number(original_path.name)
            
            if episode_num is not None:
                # Replace {Episode} with the episode number (zero-padded to 2 digits)
                new_name = new_name_pattern.replace('{Episode}', f'{episode_num:02d}')
            else:
                # If no episode number found, use 01 as default
                new_name = new_name_pattern.replace('{Episode}', '01')
            
            new_path = original_path.parent / new_name
            
            # Avoid overwriting existing files
            counter = 1
            while new_path.exists():
                name_parts = new_name.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_name_with_counter = f"{name_parts[0]}_{counter}.{name_parts[1]}"
                else:
                    new_name_with_counter = f"{new_name}_{counter}"
                new_path = original_path.parent / new_name_with_counter
                counter += 1
            
            original_path.rename(new_path)
            return str(new_path)
            
        except Exception as e:
            print(f"Error renaming file: {e}")
            return None
    
    def cleanup_file(self, file_path: str):
        """Remove file"""
        try:
            os.remove(file_path)
        except:
            pass