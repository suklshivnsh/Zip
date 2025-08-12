#!/usr/bin/env python3
"""
Test script to demonstrate the Telegram ZIP Bot functionality
"""

import asyncio
import tempfile
import zipfile
import os
from pathlib import Path

# Import bot modules
from episode_detector import EpisodeDetector
from file_processor import FileProcessor
from progress_tracker import ProgressTracker
from thumbnail_handler import ThumbnailHandler
from utils import format_file_size, is_media_file

async def create_test_zip():
    """Create a test ZIP file with sample media files."""
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "test_media.zip")
    
    # Create sample files
    sample_files = [
        "Breaking.Bad.S01E01.Pilot.720p.BluRay.x264-DEMAND.mkv",
        "Game.of.Thrones.S08E06.The.Iron.Throne.1080p.WEB.H264-MEMENTO.mp4",
        "The.Office.US.S02E03.The.Convention.DVDRip.XviD-SAiNTS.avi",
        "Stranger.Things.S04E09.Chapter.Nine.2160p.NF.WEB-DL.x265.10bit.HDR.DDP5.1.Atmos-TEPES.mkv",
        "Breaking.Bad.S01E01.Commentary.mp3",
        "Game.of.Thrones.S08E06.English.srt"
    ]
    
    # Create ZIP with sample content
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for filename in sample_files:
            # Create dummy content for each file
            content = f"Sample content for {filename}"
            zipf.writestr(filename, content.encode())
    
    return zip_path

async def main():
    """Demonstrate the complete ZIP bot workflow."""
    print("🤖 Telegram ZIP Bot - Complete Workflow Demo")
    print("=" * 50)
    
    # 1. Create components
    print("\n📦 Initializing components...")
    episode_detector = EpisodeDetector()
    file_processor = FileProcessor(episode_detector)
    thumbnail_handler = ThumbnailHandler()
    
    # Set custom settings
    episode_detector.set_channel("@MyChannel")
    episode_detector.set_rename_template("[{Quality}] {ShowName} - S{Season}E{Episode} @{Channel}.{Extension}")
    
    print("✅ Components initialized")
    
    # 2. Create test ZIP
    print("\n🗜️ Creating test ZIP file...")
    zip_path = await create_test_zip()
    zip_size = os.path.getsize(zip_path)
    print(f"✅ Test ZIP created: {format_file_size(zip_size)}")
    
    # 3. Preview processing
    print("\n👀 Previewing ZIP contents...")
    preview = file_processor.get_processing_preview(zip_path)
    
    print(f"📊 ZIP Analysis:")
    print(f"   Valid ZIP: {preview['valid_zip']}")
    print(f"   Total files: {preview['total_files']}")
    print(f"   Media files: {preview['media_files']}")
    print(f"   Estimated size: {format_file_size(preview['estimated_size'])}")
    
    print(f"\n📝 Rename Preview:")
    for file_info in preview['file_list']:
        print(f"   📁 {file_info['original']}")
        print(f"   ➡️  {file_info['new']}")
        print(f"   📊 {file_info['type']} - {format_file_size(file_info['size'])}")
        print()
    
    # 4. Create progress tracker
    print("📊 Setting up progress tracking...")
    
    def progress_callback(message):
        print(f"📈 Progress Update:\n{message}\n")
    
    progress_tracker = ProgressTracker(progress_callback)
    
    # 5. Process ZIP file
    print("🔄 Processing ZIP file...")
    result = await file_processor.process_zip_file(
        zip_path, 
        progress_tracker, 
        rename_files=True
    )
    
    # 6. Display results
    print("\n📋 Processing Results:")
    print(f"✅ Success: {result.success}")
    print(f"📦 Files processed: {len(result.processed_files)}")
    print(f"📊 Total size: {format_file_size(result.total_size)}")
    print(f"❌ Errors: {len(result.errors)}")
    
    if result.processed_files:
        print(f"\n📄 Processed Files:")
        for pfile in result.processed_files:
            print(f"   📁 {pfile.filename}")
            print(f"   ➡️  {pfile.new_filename}")
            print(f"   📊 Type: {pfile.file_type}, Size: {format_file_size(pfile.size)}")
            if pfile.episode_info:
                info = pfile.episode_info
                print(f"   🎬 S{info.season:02d}E{info.episode:02d} - {info.show_name}")
                print(f"   🎥 Quality: {info.quality}, Audio: {info.audio}")
            print()
    
    if result.errors:
        print(f"\n❌ Errors encountered:")
        for error in result.errors:
            print(f"   {error}")
    
    # 7. Cleanup
    print("🧹 Cleaning up...")
    file_processor.cleanup_temp_files()
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    print("\n🎉 Demo completed successfully!")
    print("\nThe bot is ready to process real ZIP files from Telegram!")

if __name__ == "__main__":
    asyncio.run(main())