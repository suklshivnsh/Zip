import time
import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from utils import format_file_size, format_duration, create_progress_bar
from config import Config

logger = logging.getLogger(__name__)

@dataclass
class ProgressStats:
    """Statistics for progress tracking."""
    total_files: int = 0
    processed_files: int = 0
    total_size: int = 0
    processed_size: int = 0
    start_time: float = field(default_factory=time.time)
    current_file: str = ""
    speed_bytes_per_sec: float = 0.0
    eta_seconds: Optional[int] = None
    last_update: float = field(default_factory=time.time)
    
class ProgressTracker:
    """Tracks and displays progress for file operations with ETA."""
    
    def __init__(self, update_callback: Optional[Callable[[str], None]] = None):
        self.update_callback = update_callback
        self.stats = ProgressStats()
        self.is_active = False
        self.update_task: Optional[asyncio.Task] = None
        self.files_since_update = 0
        
    def start(self, total_files: int, total_size: int = 0) -> None:
        """Start progress tracking."""
        self.stats = ProgressStats()
        self.stats.total_files = total_files
        self.stats.total_size = total_size
        self.stats.start_time = time.time()
        self.stats.last_update = time.time()
        self.is_active = True
        self.files_since_update = 0
        
        logger.info(f"Started progress tracking: {total_files} files, {format_file_size(total_size)}")
        
        # Start periodic updates if callback is provided
        if self.update_callback:
            self.update_task = asyncio.create_task(self._periodic_update())
            
    def update_file_progress(self, filename: str, file_size: int = 0, completed: bool = False) -> None:
        """Update progress for current file."""
        if not self.is_active:
            return
            
        self.stats.current_file = filename
        
        if completed:
            self.stats.processed_files += 1
            self.stats.processed_size += file_size
            self.files_since_update += 1
            
            # Calculate speed and ETA
            self._calculate_speed_and_eta()
            
            logger.info(f"File completed: {filename} ({self.stats.processed_files}/{self.stats.total_files})")
            
            # Update status after specified number of files
            if self.files_since_update >= Config.STATUS_UPDATE_FILES and self.update_callback:
                self._send_update()
                self.files_since_update = 0
                
    def _calculate_speed_and_eta(self) -> None:
        """Calculate upload speed and ETA."""
        current_time = time.time()
        elapsed_time = current_time - self.stats.start_time
        
        if elapsed_time > 0:
            # Calculate speed based on processed size
            if self.stats.processed_size > 0:
                self.stats.speed_bytes_per_sec = self.stats.processed_size / elapsed_time
            
            # Calculate ETA based on files or size
            if self.stats.processed_files > 0:
                # Use files-based calculation
                files_per_second = self.stats.processed_files / elapsed_time
                remaining_files = self.stats.total_files - self.stats.processed_files
                
                if files_per_second > 0:
                    self.stats.eta_seconds = int(remaining_files / files_per_second)
                    
            elif self.stats.speed_bytes_per_sec > 0 and self.stats.total_size > 0:
                # Use size-based calculation
                remaining_size = self.stats.total_size - self.stats.processed_size
                self.stats.eta_seconds = int(remaining_size / self.stats.speed_bytes_per_sec)
                
    def get_progress_message(self) -> str:
        """Generate progress message with visual elements."""
        if not self.is_active:
            return "Progress tracking not active"
            
        # File progress
        files_progress = create_progress_bar(self.stats.processed_files, self.stats.total_files)
        files_text = f"Files: {self.stats.processed_files}/{self.stats.total_files}"
        
        # Size progress (if available)
        size_text = ""
        if self.stats.total_size > 0:
            size_progress = create_progress_bar(self.stats.processed_size, self.stats.total_size)
            size_text = f"\nSize: {format_file_size(self.stats.processed_size)}/{format_file_size(self.stats.total_size)}\n{size_progress}"
            
        # Speed and ETA
        speed_text = ""
        if self.stats.speed_bytes_per_sec > 0:
            speed_text = f"\nSpeed: {format_file_size(int(self.stats.speed_bytes_per_sec))}/s"
            
        eta_text = ""
        if self.stats.eta_seconds is not None:
            eta_text = f"\nETA: {format_duration(self.stats.eta_seconds)}"
            
        # Current file
        current_file_text = ""
        if self.stats.current_file:
            # Truncate filename if too long
            display_name = self.stats.current_file
            if len(display_name) > 30:
                display_name = display_name[:27] + "..."
            current_file_text = f"\nCurrent: {display_name}"
            
        # Elapsed time
        elapsed = int(time.time() - self.stats.start_time)
        elapsed_text = f"\nElapsed: {format_duration(elapsed)}"
        
        return f"📊 **Upload Progress**\n\n{files_text}\n{files_progress}{size_text}{speed_text}{eta_text}{current_file_text}{elapsed_text}"
        
    def _send_update(self) -> None:
        """Send progress update via callback."""
        if self.update_callback:
            message = self.get_progress_message()
            try:
                self.update_callback(message)
            except Exception as e:
                logger.error(f"Error sending progress update: {e}")
                
    async def _periodic_update(self) -> None:
        """Periodically send progress updates."""
        while self.is_active:
            try:
                await asyncio.sleep(Config.PROGRESS_UPDATE_INTERVAL)
                if self.is_active:
                    self._send_update()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic update: {e}")
                
    def finish(self, success: bool = True) -> str:
        """Finish progress tracking and return final message."""
        if not self.is_active:
            return "Progress tracking was not active"
            
        self.is_active = False
        
        # Cancel periodic updates
        if self.update_task:
            self.update_task.cancel()
            
        # Calculate final stats
        elapsed = int(time.time() - self.stats.start_time)
        
        if success:
            status_icon = "✅"
            status_text = "Completed Successfully"
        else:
            status_icon = "❌"
            status_text = "Completed with Errors"
            
        # Generate final message
        final_message = f"{status_icon} **{status_text}**\n\n"
        final_message += f"Files Processed: {self.stats.processed_files}/{self.stats.total_files}\n"
        
        if self.stats.total_size > 0:
            final_message += f"Data Processed: {format_file_size(self.stats.processed_size)}\n"
            
        final_message += f"Total Time: {format_duration(elapsed)}\n"
        
        if self.stats.speed_bytes_per_sec > 0:
            avg_speed = format_file_size(int(self.stats.speed_bytes_per_sec))
            final_message += f"Average Speed: {avg_speed}/s\n"
            
        logger.info(f"Progress tracking finished: {self.stats.processed_files}/{self.stats.total_files} files in {elapsed}s")
        
        return final_message
        
    def pause(self) -> None:
        """Pause progress tracking."""
        self.is_active = False
        if self.update_task:
            self.update_task.cancel()
            
    def resume(self) -> None:
        """Resume progress tracking."""
        if not self.is_active:
            self.is_active = True
            # Restart periodic updates if callback is available
            if self.update_callback:
                self.update_task = asyncio.create_task(self._periodic_update())
                
    def get_current_stats(self) -> Dict[str, Any]:
        """Get current progress statistics."""
        elapsed = time.time() - self.stats.start_time
        
        return {
            'total_files': self.stats.total_files,
            'processed_files': self.stats.processed_files,
            'total_size': self.stats.total_size,
            'processed_size': self.stats.processed_size,
            'elapsed_seconds': elapsed,
            'current_file': self.stats.current_file,
            'speed_bytes_per_sec': self.stats.speed_bytes_per_sec,
            'eta_seconds': self.stats.eta_seconds,
            'is_active': self.is_active,
            'progress_percentage': (self.stats.processed_files / self.stats.total_files * 100) if self.stats.total_files > 0 else 0
        }
        
    def add_error(self, error_message: str, filename: str = "") -> None:
        """Add an error to the progress tracking."""
        error_text = f"Error processing {filename}: {error_message}" if filename else f"Error: {error_message}"
        logger.error(error_text)
        
        # Could extend this to collect errors for final report
        
class BatchProgressTracker:
    """Manages progress tracking for multiple concurrent operations."""
    
    def __init__(self):
        self.trackers: Dict[str, ProgressTracker] = {}
        
    def create_tracker(self, task_id: str, update_callback: Optional[Callable[[str], None]] = None) -> ProgressTracker:
        """Create a new progress tracker for a task."""
        tracker = ProgressTracker(update_callback)
        self.trackers[task_id] = tracker
        return tracker
        
    def get_tracker(self, task_id: str) -> Optional[ProgressTracker]:
        """Get existing progress tracker."""
        return self.trackers.get(task_id)
        
    def remove_tracker(self, task_id: str) -> None:
        """Remove and cleanup a progress tracker."""
        if task_id in self.trackers:
            tracker = self.trackers[task_id]
            tracker.finish()
            del self.trackers[task_id]
            
    def get_all_active_trackers(self) -> Dict[str, ProgressTracker]:
        """Get all currently active trackers."""
        return {task_id: tracker for task_id, tracker in self.trackers.items() if tracker.is_active}
        
    def cleanup_finished_trackers(self) -> None:
        """Clean up all finished trackers."""
        finished_tasks = [task_id for task_id, tracker in self.trackers.items() if not tracker.is_active]
        for task_id in finished_tasks:
            del self.trackers[task_id]