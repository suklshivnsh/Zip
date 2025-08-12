#!/usr/bin/env python3
"""
Demo script to showcase the Telegram Bot functionality
"""

import os
import tempfile
import zipfile
from pathlib import Path
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_handler import FileHandler

def create_sample_zip():
    """Create a sample zip file with test video files"""
    print("📦 Creating sample zip file...")
    
    temp_dir = tempfile.mkdtemp()
    handler = FileHandler(temp_dir, temp_dir)
    
    # Create sample anime episode files
    sample_files = [
        "Suspicious Maid E01 Raw.mkv",
        "Suspicious Maid E02 Raw.mkv", 
        "Suspicious Maid E03 Raw.mkv",
        "Some Show Episode 5 720p.mp4",
        "Another Series [S1E07] HDTV.avi"
    ]
    
    zip_path = os.path.join(temp_dir, "anime_episodes.zip")
    
    # Create test zip
    with zipfile.ZipFile(zip_path, 'w') as zip_ref:
        for filename in sample_files:
            file_path = os.path.join(temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write(f"Sample content for {filename}")
            zip_ref.write(file_path, filename)
            os.remove(file_path)
    
    print(f"✅ Created zip file: {zip_path}")
    return zip_path, handler

def demo_extraction_and_renaming():
    """Demonstrate the extraction and renaming process"""
    print("\n🚀 Demonstrating Zip Extraction with Episode Detection\n")
    
    zip_path, handler = create_sample_zip()
    
    # Demonstrate zip validation
    print("🔍 Validating zip file...")
    is_valid_zip = handler.is_zip_file(zip_path)
    print(f"✅ Valid zip file: {is_valid_zip}")
    
    # Extract the zip
    print("\n📂 Extracting zip file...")
    extracted_files = handler.extract_zip(zip_path)
    print(f"✅ Extracted {len(extracted_files)} files:")
    for file_path in extracted_files:
        if os.path.isfile(file_path):
            print(f"   📄 {os.path.basename(file_path)}")
    
    # Demonstrate episode detection
    print("\n🎯 Detecting episode numbers...")
    for file_path in extracted_files:
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            episode_num = handler.detect_episode_number(filename)
            print(f"   📺 {filename} -> Episode: {episode_num if episode_num else 'Not detected'}")
    
    # Demonstrate renaming with pattern
    print("\n🏷️  Renaming files with custom pattern...")
    pattern = "Suspicious Maid [S1 - E{Episode}] [480p] [MultiAudio] @Animejunctions2.mkv"
    
    renamed_files = []
    for file_path in extracted_files:
        if os.path.isfile(file_path):
            original_name = os.path.basename(file_path)
            renamed_path = handler.rename_with_episode(file_path, pattern)
            if renamed_path:
                new_name = os.path.basename(renamed_path)
                renamed_files.append(renamed_path)
                print(f"   ✅ {original_name}")
                print(f"      -> {new_name}")
            else:
                print(f"   ❌ Failed to rename: {original_name}")
    
    print(f"\n✅ Successfully processed {len(renamed_files)} files!")
    
    # Show final results
    print("\n📋 Final Results:")
    for renamed_file in renamed_files:
        if os.path.isfile(renamed_file):
            print(f"   📄 {os.path.basename(renamed_file)}")
    
    # Cleanup
    import shutil
    shutil.rmtree(os.path.dirname(zip_path))

def demo_bot_commands():
    """Show what bot commands would look like"""
    print("\n🤖 Bot Command Examples:\n")
    
    commands = [
        ("/start", "Welcome message and bot introduction"),
        ("/help", "Detailed help and usage instructions"),
        ("/e Suspicious Maid [S1 - E{Episode}] [480p] [MultiAudio] @Animejunctions2.mkv", 
         "Set pattern for extraction and renaming"),
        ("Send zip file", "Bot extracts and processes according to set pattern"),
        ("Send URL to zip", "Bot downloads, extracts, and processes the file")
    ]
    
    for command, description in commands:
        print(f"📱 {command}")
        print(f"   💬 {description}\n")

def main():
    """Run the demonstration"""
    print("🎬 Telegram Zip Extraction Bot - Demonstration\n")
    
    try:
        demo_extraction_and_renaming()
        demo_bot_commands()
        
        print("\n" + "="*60)
        print("✨ Demo completed successfully!")
        print("📖 Check README.md for setup instructions")
        print("🚀 Run 'python main.py' to start the actual bot")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())