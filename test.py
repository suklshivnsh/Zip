#!/usr/bin/env python3
"""
Test script for the Zip Extraction Bot functionality
"""

import sys
import os
import tempfile
import zipfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_handler import FileHandler

def test_episode_detection():
    """Test episode number detection from various filename formats"""
    print("Testing episode detection...")
    
    # Create a temporary file handler
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = FileHandler(temp_dir, temp_dir)
        
        test_cases = [
            ("Suspicious Maid E01 720p.mkv", 1),
            ("anime_s01e05_480p.mp4", 5),
            ("Show Name [Episode 12] [1080p].mkv", 12),
            ("Series - 03 - Title.avi", 3),
            ("Movie.Name.2023.E07.WEBRip.mkv", 7),
            ("Random Show Episode 15 HD.mp4", 15),
            ("NoEpisode.mkv", None),
            ("[02] Title Name.mkv", 2),
        ]
        
        for filename, expected in test_cases:
            result = handler.detect_episode_number(filename)
            status = "✅" if result == expected else "❌"
            print(f"{status} {filename} -> {result} (expected: {expected})")
        
        print()

def test_zip_operations():
    """Test zip file creation and extraction"""
    print("Testing zip operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        handler = FileHandler(temp_dir, temp_dir)
        
        # Create test files
        test_files = [
            "Test Show E01.mkv",
            "Test Show E02.mkv", 
            "Test Show E03.mkv"
        ]
        
        zip_path = os.path.join(temp_dir, "test.zip")
        
        # Create a test zip file
        with zipfile.ZipFile(zip_path, 'w') as zip_ref:
            for filename in test_files:
                file_path = os.path.join(temp_dir, filename)
                # Create empty test files
                with open(file_path, 'w') as f:
                    f.write("test content")
                zip_ref.write(file_path, filename)
                os.remove(file_path)  # Remove original after adding to zip
        
        # Test zip detection
        is_zip = handler.is_zip_file(zip_path)
        print(f"✅ Zip detection: {is_zip}")
        
        # Test extraction
        extracted_files = handler.extract_zip(zip_path)
        print(f"✅ Extracted {len(extracted_files)} files")
        
        # Test renaming with pattern
        pattern = "New Show [S1 - E{Episode}] [720p].mkv"
        for extracted_file in extracted_files:
            if os.path.isfile(extracted_file):
                renamed = handler.rename_with_episode(extracted_file, pattern)
                if renamed:
                    print(f"✅ Renamed: {os.path.basename(extracted_file)} -> {os.path.basename(renamed)}")
        
        print()

def test_config_validation():
    """Test configuration validation"""
    print("Testing configuration...")
    
    from config import Config
    
    # Test with empty config (should fail)
    original_values = (Config.API_ID, Config.API_HASH, Config.BOT_TOKEN)
    
    Config.API_ID = 0
    Config.API_HASH = ""
    Config.BOT_TOKEN = ""
    
    is_valid = Config.validate()
    print(f"❌ Empty config validation: {is_valid} (should be False)")
    
    # Restore original values
    Config.API_ID, Config.API_HASH, Config.BOT_TOKEN = original_values
    
    print()

def main():
    """Run all tests"""
    print("🤖 Zip Extraction Bot - Test Suite\n")
    
    try:
        test_episode_detection()
        test_zip_operations()
        test_config_validation()
        
        print("✅ All tests completed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())