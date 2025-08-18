import asyncio
import logging
import os
import re
from pathlib import Path
from typing import Optional

from pyrogram import Client, filters
from pyrogram.types import Message

from config import Config
from file_handler import FileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ZipExtractionBot:
    """Telegram Bot for Zip Extraction with Episode Detection"""
    
    def __init__(self):
        # Validate configuration
        if not Config.validate():
            raise ValueError("Invalid configuration. Please check API_ID, API_HASH, and BOT_TOKEN.")
        
        # Initialize Pyrogram client
        self.app = Client(
            "zip_extraction_bot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN
        )
        
        # Initialize file handler
        self.file_handler = FileHandler(Config.DOWNLOAD_PATH, Config.EXTRACT_PATH)
        
        # Register handlers
        self.register_handlers()
    
    def register_handlers(self):
        """Register message handlers"""
        
        @self.app.on_message(filters.command("start"))
        async def start_command(client, message: Message):
            welcome_text = """
🤖 **Zip Extraction Bot**

Welcome! I can help you extract zip files and rename them with episode detection.

**Commands:**
• Send me a zip file directly
• Send me a link to a zip file
• Use `/e filename_pattern` to extract and rename files

**Example:**
`/e Suspicious Maid [S1 - E{Episode}] [480p] [MultiAudio] @Animejunctions2.mkv`

The `{Episode}` placeholder will be replaced with the detected episode number.
            """
            await message.reply_text(welcome_text)
        
        @self.app.on_message(filters.command("help"))
        async def help_command(client, message: Message):
            help_text = """
📋 **Help - How to use this bot:**

**1. Direct Zip Upload:**
Just send me a zip file and I'll extract it for you.

**2. External Link:**
Send me a direct link to a zip file and I'll download and extract it.

**3. Extract with Rename (Advanced):**
Use the `/e` command followed by your desired filename pattern:

`/e New Filename [S1 - E{Episode}] [720p].mkv`

The bot will:
• Download/extract the zip file
• Detect episode numbers from filenames
• Rename files according to your pattern
• Replace `{Episode}` with the detected episode number

**Episode Detection:**
The bot can detect episode numbers from various formats:
• E01, e01
• Episode 01
• S01E01
• [01]
• Standalone numbers
            """
            await message.reply_text(help_text)
        
        @self.app.on_message(filters.command("e"))
        async def extract_command(client, message: Message):
            """Handle /e command for extraction with renaming"""
            if len(message.command) < 2:
                await message.reply_text("❌ Please provide a filename pattern.\n\nExample: `/e Suspicious Maid [S1 - E{Episode}] [480p] @Animejunctions2.mkv`")
                return
            
            # Get the filename pattern
            filename_pattern = " ".join(message.command[1:])
            
            # Store the pattern for the next file upload
            user_id = message.from_user.id
            self.store_user_pattern(user_id, filename_pattern)
            
            await message.reply_text(f"✅ Pattern set: `{filename_pattern}`\n\nNow send me a zip file or link to process!")
        
        @self.app.on_message(filters.document)
        async def handle_document(client, message: Message):
            """Handle document uploads"""
            document = message.document
            
            if not document.file_name:
                await message.reply_text("❌ File must have a filename.")
                return
            
            if document.file_size > Config.MAX_FILE_SIZE:
                await message.reply_text(f"❌ File too large. Maximum size: {Config.MAX_FILE_SIZE // (1024*1024)}MB")
                return
            
            # Check if it's a zip file
            if not (document.file_name.lower().endswith('.zip') or 
                   document.mime_type in ['application/zip', 'application/x-zip-compressed']):
                await message.reply_text("❌ Please send a zip file.")
                return
            
            await self.process_zip_file(message, document=document)
        
        @self.app.on_message(filters.text & ~filters.command(["start", "help", "e"]))
        async def handle_text(client, message: Message):
            """Handle text messages (potential links)"""
            text = message.text.strip()
            
            # Check if it's a URL
            url_pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?[\w&=%.]*)?)?)?' 
            if re.match(url_pattern, text):
                await self.process_zip_file(message, url=text)
            else:
                await message.reply_text("❌ Please send a zip file, a direct link to a zip file, or use `/help` for more information.")
    
    def store_user_pattern(self, user_id: int, pattern: str):
        """Store user's filename pattern (simple in-memory storage)"""
        if not hasattr(self, 'user_patterns'):
            self.user_patterns = {}
        self.user_patterns[user_id] = pattern
    
    def get_user_pattern(self, user_id: int) -> Optional[str]:
        """Get user's stored filename pattern"""
        if hasattr(self, 'user_patterns'):
            return self.user_patterns.get(user_id)
        return None
    
    async def process_zip_file(self, message: Message, document=None, url=None):
        """Process zip file from document or URL"""
        status_message = await message.reply_text("🔄 Processing...")
        
        try:
            file_path = None
            
            if document:
                # Download the document
                await status_message.edit_text("📥 Downloading file...")
                file_path = await message.download(
                    file_name=str(self.file_handler.download_path / document.file_name)
                )
            
            elif url:
                # Download from URL
                await status_message.edit_text("📥 Downloading from URL...")
                file_path = await self.file_handler.download_file(url)
                
                if not file_path:
                    await status_message.edit_text("❌ Failed to download file from URL.")
                    return
            
            if not file_path:
                await status_message.edit_text("❌ Failed to download file.")
                return
            
            # Verify it's a zip file
            if not self.file_handler.is_zip_file(file_path):
                await status_message.edit_text("❌ File is not a valid zip file.")
                self.file_handler.cleanup_file(file_path)
                return
            
            # Extract the zip file
            await status_message.edit_text("📦 Extracting zip file...")
            extracted_files = self.file_handler.extract_zip(file_path)
            
            if not extracted_files:
                await status_message.edit_text("❌ Failed to extract zip file or no files found.")
                self.file_handler.cleanup_file(file_path)
                return
            
            # Get user's pattern if exists
            user_pattern = self.get_user_pattern(message.from_user.id)
            
            # Process extracted files
            await status_message.edit_text("🔄 Processing extracted files...")
            
            processed_files = []
            for file_path_extracted in extracted_files:
                if os.path.isfile(file_path_extracted):
                    if user_pattern:
                        # Rename according to pattern
                        renamed_file = self.file_handler.rename_with_episode(file_path_extracted, user_pattern)
                        if renamed_file:
                            processed_files.append(renamed_file)
                        else:
                            processed_files.append(file_path_extracted)
                    else:
                        processed_files.append(file_path_extracted)
            
            # Upload processed files
            await status_message.edit_text("📤 Uploading files...")
            
            for processed_file in processed_files:
                if os.path.isfile(processed_file):
                    file_size = os.path.getsize(processed_file)
                    if file_size <= Config.MAX_FILE_SIZE:
                        try:
                            await message.reply_document(
                                document=processed_file,
                                caption=f"📁 Extracted: {os.path.basename(processed_file)}"
                            )
                        except Exception as e:
                            logger.error(f"Error uploading file {processed_file}: {e}")
                            await message.reply_text(f"❌ Failed to upload: {os.path.basename(processed_file)}")
                    else:
                        await message.reply_text(f"❌ File too large to upload: {os.path.basename(processed_file)}")
            
            # Cleanup
            self.file_handler.cleanup_file(file_path)
            for processed_file in processed_files:
                self.file_handler.cleanup_file(processed_file)
            
            await status_message.edit_text(f"✅ Successfully processed {len(processed_files)} file(s)!")
            
            # Clear user pattern after use
            if user_pattern and hasattr(self, 'user_patterns'):
                del self.user_patterns[message.from_user.id]
                
        except Exception as e:
            logger.error(f"Error processing zip file: {e}")
            await status_message.edit_text(f"❌ Error processing file: {str(e)}")
    
    def run(self):
        """Start the bot"""
        logger.info("Starting Zip Extraction Bot...")
        self.app.run()

def main():
    """Main entry point"""
    try:
        bot = ZipExtractionBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Bot error: {e}")

if __name__ == "__main__":
    main()