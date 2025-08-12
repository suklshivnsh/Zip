#!/usr/bin/env python3
"""
Telegram ZIP Bot - Extract and process ZIP files with episode detection and custom thumbnails.
"""

import os
import sys
import asyncio
import logging
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime

# Telegram bot imports
from telegram import Update, Message, Document, InputMediaVideo, InputMediaDocument
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    CallbackContext
)
from telegram.constants import ParseMode

# Local imports
from config import Config
from utils import (
    format_file_size, 
    is_media_file, 
    split_message,
    clean_temp_files
)
from file_processor import FileProcessor, ProcessingResult
from episode_detector import EpisodeDetector
from thumbnail_handler import ThumbnailHandler
from progress_tracker import ProgressTracker, BatchProgressTracker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ZipBot:
    """Main Telegram Bot class for ZIP file processing."""
    
    def __init__(self):
        self.file_processor = FileProcessor()
        self.episode_detector = EpisodeDetector()
        self.thumbnail_handler = ThumbnailHandler()
        self.progress_manager = BatchProgressTracker()
        self.user_settings: Dict[int, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        
        # Create default thumbnail
        self.thumbnail_handler.create_default_thumbnail()
        
    def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings with defaults."""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = {
                'dump_channel': Config.DUMP_CHANNEL_ID,
                'rename_template': Config.DEFAULT_RENAME_TEMPLATE,
                'channel_name': 'Channel',
                'auto_rename': True
            }
        return self.user_settings[user_id]
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        welcome_text = f"""
🤖 **ZIP Bot** - Welcome {user.first_name}!

I can help you extract and process ZIP files with advanced features:

📁 **Features:**
• Extract ZIP files and organize contents
• Smart episode detection and renaming
• Custom thumbnails for uploads
• Progress tracking with ETA
• Dump channel support

🎯 **Commands:**
/help - Show detailed help
/e <template> - Set rename template
/t - Set custom thumbnail (reply to image)
/channel <name> - Set channel name for renaming
/dump <chat_id> - Set dump channel
/settings - View current settings
/preview - Preview how files will be renamed

📤 **Usage:**
Just send me a ZIP file or a link to one, and I'll process it for you!
        """
        
        await update.message.reply_text(
            welcome_text.strip(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        help_text = """
🔧 **Detailed Help**

**📁 ZIP File Processing:**
• Send a ZIP file directly or paste a download link
• Bot will extract and detect episodes automatically
• Supports video, audio, and subtitle files

**🎬 Episode Detection:**
• Automatically detects: S01E01, 1x01, Episode 1, etc.
• Extracts show name, quality, and audio info
• Smart renaming with customizable templates

**📋 Rename Templates:**
Use `/e <template>` to set custom naming:
• `{Season}` - Season number (01, 02, etc.)
• `{Episode}` - Episode number (01, 02, etc.)
• `{ShowName}` - Detected show name
• `{Quality}` - Video quality (720p, 1080p, etc.)
• `{Audio}` - Audio format (AAC, AC3, etc.)
• `{Channel}` - Your channel name
• `{Extension}` - File extension

**Default template:**
`[S{Season} - E{Episode}] {ShowName} [{Quality}] [{Audio}] @{Channel}.{Extension}`

**🖼️ Custom Thumbnails:**
• Use `/t` command and reply to an image
• Thumbnails will be used for all uploads
• Supports JPEG, PNG, WebP formats

**⚙️ Settings Commands:**
• `/channel <name>` - Set channel name for @mentions
• `/dump <chat_id>` - Set dump channel for uploads
• `/settings` - View all current settings
• `/preview` - Preview file renaming

**📊 Progress Features:**
• Real-time progress bars with ETA
• Upload speed monitoring
• Updates every 5 seconds during processing
• Status updates after every 4 files

**🔧 Admin Commands:**
• `/cleanup` - Clean temporary files
• `/stats` - Show bot statistics
        """
        
        messages = split_message(help_text.strip())
        for message in messages:
            await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)
            
    async def rename_template_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /e command to set rename template."""
        user_id = update.effective_user.id
        
        if not context.args:
            current_template = self.get_user_settings(user_id)['rename_template']
            await update.message.reply_text(
                f"**Current rename template:**\n`{current_template}`\n\n"
                f"Use `/e <template>` to set a new template.\n\n"
                f"**Available variables:**\n"
                f"• `{{Season}}` - Season number\n"
                f"• `{{Episode}}` - Episode number\n"
                f"• `{{ShowName}}` - Show name\n"
                f"• `{{Quality}}` - Video quality\n"
                f"• `{{Audio}}` - Audio format\n"
                f"• `{{Channel}}` - Channel name\n"
                f"• `{{Extension}}` - File extension",
                parse_mode=ParseMode.MARKDOWN
            )
            return
            
        new_template = ' '.join(context.args)
        self.get_user_settings(user_id)['rename_template'] = new_template
        self.episode_detector.set_rename_template(new_template)
        
        await update.message.reply_text(
            f"✅ **Rename template updated:**\n`{new_template}`",
            parse_mode=ParseMode.MARKDOWN
        )
        
    async def thumbnail_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /t command for setting custom thumbnail."""
        user_id = update.effective_user.id
        
        # Check if replying to a photo
        if update.message.reply_to_message and update.message.reply_to_message.photo:
            try:
                # Get the largest photo
                photo = update.message.reply_to_message.photo[-1]
                file = await context.bot.get_file(photo.file_id)
                
                # Download photo data
                file_data = await file.download_as_bytearray()
                
                # Save as custom thumbnail
                success = self.thumbnail_handler.save_thumbnail_from_telegram(
                    user_id, file.file_path, bytes(file_data)
                )
                
                if success:
                    await update.message.reply_text(
                        "✅ **Custom thumbnail set successfully!**\n"
                        "This thumbnail will be used for all your uploads.",
                        parse_mode=ParseMode.MARKDOWN
                    )
                else:
                    await update.message.reply_text(
                        "❌ **Error setting thumbnail.**\n"
                        "Please make sure the image is valid (JPEG/PNG/WebP)."
                    )
                    
            except Exception as e:
                logger.error(f"Error setting thumbnail for user {user_id}: {e}")
                await update.message.reply_text(
                    "❌ **Error processing thumbnail.**\n"
                    "Please try again with a different image."
                )
        else:
            # Show current thumbnail info
            thumb_info = self.thumbnail_handler.get_thumbnail_info(user_id)
            
            if thumb_info['has_thumbnail']:
                size_text = format_file_size(thumb_info['size'])
                dims_text = f"{thumb_info['dimensions'][0]}x{thumb_info['dimensions'][1]}"
                
                await update.message.reply_text(
                    f"🖼️ **Current Custom Thumbnail:**\n"
                    f"Size: {size_text}\n"
                    f"Dimensions: {dims_text}\n\n"
                    f"Reply to this command with a photo to change it.\n"
                    f"Use `/t remove` to remove custom thumbnail.",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text(
                    "📷 **No custom thumbnail set.**\n\n"
                    "Reply to this command with a photo to set a custom thumbnail.\n"
                    "Supported formats: JPEG, PNG, WebP"
                )
                
        # Handle thumbnail removal
        if context.args and context.args[0].lower() == 'remove':
            if self.thumbnail_handler.remove_user_thumbnail(user_id):
                await update.message.reply_text(
                    "✅ **Custom thumbnail removed.**\n"
                    "Default thumbnail will be used for uploads."
                )
            else:
                await update.message.reply_text("ℹ️ No custom thumbnail to remove.")
                
    async def channel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /channel command to set channel name."""
        user_id = update.effective_user.id
        
        if not context.args:
            current_channel = self.get_user_settings(user_id)['channel_name']
            await update.message.reply_text(
                f"**Current channel name:** `{current_channel}`\n\n"
                f"Use `/channel <name>` to set a new channel name.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
            
        new_channel = ' '.join(context.args)
        self.get_user_settings(user_id)['channel_name'] = new_channel
        self.episode_detector.set_channel(new_channel)
        
        await update.message.reply_text(
            f"✅ **Channel name updated:** `{new_channel}`",
            parse_mode=ParseMode.MARKDOWN
        )
        
    async def dump_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /dump command to set dump channel."""
        user_id = update.effective_user.id
        
        if not context.args:
            current_dump = self.get_user_settings(user_id)['dump_channel']
            dump_text = current_dump if current_dump else "Not set"
            
            await update.message.reply_text(
                f"**Current dump channel:** `{dump_text}`\n\n"
                f"Use `/dump <chat_id>` to set dump channel.\n"
                f"Use `/dump remove` to disable dump channel.",
                parse_mode=ParseMode.MARKDOWN
            )
            return
            
        if context.args[0].lower() == 'remove':
            self.get_user_settings(user_id)['dump_channel'] = None
            await update.message.reply_text("✅ **Dump channel removed.**")
            return
            
        try:
            chat_id = int(context.args[0])
            self.get_user_settings(user_id)['dump_channel'] = chat_id
            
            await update.message.reply_text(
                f"✅ **Dump channel set:** `{chat_id}`\n"
                f"Files will be uploaded to this channel.",
                parse_mode=ParseMode.MARKDOWN
            )
        except ValueError:
            await update.message.reply_text(
                "❌ **Invalid chat ID.**\n"
                "Please provide a valid numeric chat ID."
            )
            
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /settings command to show current settings."""
        user_id = update.effective_user.id
        settings = self.get_user_settings(user_id)
        thumb_info = self.thumbnail_handler.get_thumbnail_info(user_id)
        
        dump_text = settings['dump_channel'] if settings['dump_channel'] else "Not set"
        thumb_text = "Custom set" if thumb_info['has_thumbnail'] else "Default"
        
        settings_text = f"""
⚙️ **Your Settings**

**📝 Rename Template:**
`{settings['rename_template']}`

**📺 Channel Name:**
`{settings['channel_name']}`

**📤 Dump Channel:**
`{dump_text}`

**🖼️ Thumbnail:**
`{thumb_text}`

**🔄 Auto Rename:**
`{'Enabled' if settings['auto_rename'] else 'Disabled'}`

Use the respective commands to modify these settings.
        """
        
        await update.message.reply_text(
            settings_text.strip(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle document uploads (ZIP files)."""
        user_id = update.effective_user.id
        document = update.message.document
        
        # Check if it's a ZIP file
        if not document.file_name.lower().endswith('.zip'):
            await update.message.reply_text(
                "📄 This doesn't appear to be a ZIP file.\n"
                "Please send a .zip file or use a direct download link."
            )
            return
            
        # Check file size
        if document.file_size > Config.MAX_FILE_SIZE_BYTES:
            size_limit = format_file_size(Config.MAX_FILE_SIZE_BYTES)
            file_size = format_file_size(document.file_size)
            
            await update.message.reply_text(
                f"❌ **File too large:** {file_size}\n"
                f"Maximum supported size: {size_limit}"
            )
            return
            
        # Start processing
        await self._process_zip_document(update, context, document)
        
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages (potential download links)."""
        text = update.message.text.strip()
        
        # Check if it looks like a URL
        if text.startswith(('http://', 'https://')):
            if text.lower().endswith('.zip'):
                await self._process_zip_url(update, context, text)
            else:
                await update.message.reply_text(
                    "🔗 This link doesn't appear to point to a ZIP file.\n"
                    "Please provide a direct link to a .zip file."
                )
        else:
            await update.message.reply_text(
                "❓ I can process ZIP files and download links.\n"
                "Send /help for more information."
            )
            
    async def _process_zip_document(self, 
                                  update: Update, 
                                  context: ContextTypes.DEFAULT_TYPE, 
                                  document: Document) -> None:
        """Process ZIP file from Telegram document."""
        user_id = update.effective_user.id
        
        # Create progress tracker
        def progress_update(message: str):
            asyncio.create_task(
                context.bot.edit_message_text(
                    text=message,
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    parse_mode=ParseMode.MARKDOWN
                )
            )
            
        progress_tracker = self.progress_manager.create_tracker(
            f"zip_{user_id}_{document.file_id}",
            progress_update
        )
        
        # Send initial status
        status_message = await update.message.reply_text(
            "📥 **Downloading ZIP file...**\n"
            f"File: `{document.file_name}`\n"
            f"Size: `{format_file_size(document.file_size)}`",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Download file
            file = await context.bot.get_file(document.file_id)
            temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip', dir=Config.TEMP_DIR)
            await file.download_to_drive(temp_zip.name)
            
            await context.bot.edit_message_text(
                text="📦 **Processing ZIP file...**\n"
                     "Extracting contents and detecting episodes...",
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Process ZIP
            settings = self.get_user_settings(user_id)
            result = await self.file_processor.process_zip_file(
                temp_zip.name,
                progress_tracker,
                settings['auto_rename']
            )
            
            # Upload processed files
            if result.success:
                await self._upload_processed_files(
                    update, context, result, progress_tracker
                )
            else:
                error_text = "❌ **Processing failed:**\n" + "\n".join(result.errors)
                await context.bot.edit_message_text(
                    text=error_text,
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id
                )
                
        except Exception as e:
            logger.error(f"Error processing ZIP document: {e}")
            await context.bot.edit_message_text(
                text=f"❌ **Error processing ZIP file:**\n`{str(e)}`",
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            # Cleanup
            if os.path.exists(temp_zip.name):
                os.remove(temp_zip.name)
            progress_tracker.finish()
            
    async def _process_zip_url(self, 
                             update: Update, 
                             context: ContextTypes.DEFAULT_TYPE, 
                             url: str) -> None:
        """Process ZIP file from URL."""
        user_id = update.effective_user.id
        
        # Send initial status
        status_message = await update.message.reply_text(
            f"🔗 **Downloading from URL...**\n`{url}`",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Download ZIP from URL
            zip_path = await self.file_processor.download_zip_from_url(url)
            
            if not zip_path:
                await context.bot.edit_message_text(
                    text="❌ **Failed to download ZIP file from URL.**",
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id
                )
                return
                
            # Continue with processing like document upload
            await context.bot.edit_message_text(
                text="📦 **Processing downloaded ZIP...**",
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id
            )
            
            # Create progress tracker
            def progress_update(message: str):
                asyncio.create_task(
                    context.bot.edit_message_text(
                        text=message,
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id,
                        parse_mode=ParseMode.MARKDOWN
                    )
                )
                
            progress_tracker = self.progress_manager.create_tracker(
                f"url_{user_id}_{hash(url)}",
                progress_update
            )
            
            # Process ZIP
            settings = self.get_user_settings(user_id)
            result = await self.file_processor.process_zip_file(
                zip_path,
                progress_tracker,
                settings['auto_rename']
            )
            
            # Upload processed files
            if result.success:
                await self._upload_processed_files(
                    update, context, result, progress_tracker
                )
            else:
                error_text = "❌ **Processing failed:**\n" + "\n".join(result.errors)
                await context.bot.edit_message_text(
                    text=error_text,
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id
                )
                
        except Exception as e:
            logger.error(f"Error processing ZIP URL: {e}")
            await context.bot.edit_message_text(
                text=f"❌ **Error downloading/processing ZIP:**\n`{str(e)}`",
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                parse_mode=ParseMode.MARKDOWN
            )
        finally:
            if 'zip_path' in locals() and os.path.exists(zip_path):
                os.remove(zip_path)
            if 'progress_tracker' in locals():
                progress_tracker.finish()
                
    async def _upload_processed_files(self,
                                    update: Update,
                                    context: ContextTypes.DEFAULT_TYPE,
                                    result: ProcessingResult,
                                    progress_tracker: ProgressTracker) -> None:
        """Upload processed files to Telegram."""
        user_id = update.effective_user.id
        settings = self.get_user_settings(user_id)
        
        # Determine target chat
        target_chat = settings.get('dump_channel') or update.effective_chat.id
        
        # Get user thumbnail
        thumbnail_path = self.thumbnail_handler.get_user_thumbnail(user_id)
        
        success_count = 0
        error_count = 0
        
        for processed_file in result.processed_files:
            try:
                progress_tracker.update_file_progress(
                    processed_file.new_filename,
                    processed_file.size,
                    completed=False
                )
                
                # Prepare file for upload
                with open(processed_file.new_path, 'rb') as file_data:
                    if processed_file.file_type == 'video':
                        # Upload as video
                        await context.bot.send_video(
                            chat_id=target_chat,
                            video=file_data,
                            caption=f"📺 {processed_file.new_filename}",
                            filename=processed_file.new_filename,
                            thumbnail=open(thumbnail_path, 'rb') if thumbnail_path else None,
                            supports_streaming=True
                        )
                    else:
                        # Upload as document
                        await context.bot.send_document(
                            chat_id=target_chat,
                            document=file_data,
                            caption=f"📄 {processed_file.new_filename}",
                            filename=processed_file.new_filename,
                            thumbnail=open(thumbnail_path, 'rb') if thumbnail_path else None
                        )
                        
                success_count += 1
                progress_tracker.update_file_progress(
                    processed_file.new_filename,
                    processed_file.size,
                    completed=True
                )
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error uploading {processed_file.new_filename}: {e}")
                progress_tracker.add_error(str(e), processed_file.new_filename)
                
        # Send final summary
        final_message = progress_tracker.finish(success_count > 0)
        final_message += f"\n\n📊 **Summary:**\n"
        final_message += f"✅ Successfully uploaded: {success_count}\n"
        
        if error_count > 0:
            final_message += f"❌ Failed uploads: {error_count}\n"
            
        final_message += f"📦 Total size: {format_file_size(result.total_size)}"
        
        await update.message.reply_text(final_message, parse_mode=ParseMode.MARKDOWN)
        
        # Cleanup
        self.file_processor.cleanup_temp_files()

def main():
    """Main function to run the bot."""
    # Check for required configuration
    if not Config.BOT_TOKEN:
        logger.error("BOT_TOKEN not found in environment variables")
        sys.exit(1)
        
    # Create bot instance
    bot = ZipBot()
    
    # Create application
    application = Application.builder().token(Config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("e", bot.rename_template_command))
    application.add_handler(CommandHandler("t", bot.thumbnail_command))
    application.add_handler(CommandHandler("channel", bot.channel_command))
    application.add_handler(CommandHandler("dump", bot.dump_command))
    application.add_handler(CommandHandler("settings", bot.settings_command))
    
    # Document and text handlers
    application.add_handler(MessageHandler(filters.Document.ALL, bot.handle_document))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_text_message))
    
    # Start the bot
    logger.info("Starting ZIP Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()