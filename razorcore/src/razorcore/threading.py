"""
Base QThread worker classes for background task execution.

Provides reusable worker patterns for:
- Long-running tasks with progress reporting
- Async/await task execution in Qt context
- Cancellable operations
"""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QThread, Signal, QMutex, QMutexLocker


logger = logging.getLogger(__name__)


class BaseWorker(QThread):
    """
    Base worker class for long-running operations with progress reporting.
    
    Provides:
    - Progress signals (current, total, message)
    - Log message signals
    - Cancellation support
    - Pause/resume support
    - Error handling
    
    Subclass and override `do_work()` to implement your task.
    
    Example:
        class DownloadWorker(BaseWorker):
            def do_work(self):
                for i, url in enumerate(self.urls):
                    if self.is_cancelled:
                        return
                    self.download(url)
                    self.report_progress(i + 1, len(self.urls), url)
    """
    
    # Signals
    progress = Signal(int, int, str)      # current, total, message
    log_message = Signal(str, str)        # message, level
    finished = Signal(dict)               # result dict
    error = Signal(str)                   # error message
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cancelled = False
        self._paused = False
        self._mutex = QMutex()
        self._result: Dict[str, Any] = {}
    
    @property
    def is_cancelled(self) -> bool:
        """Thread-safe check for cancellation."""
        with QMutexLocker(self._mutex):
            return self._cancelled
    
    @property
    def is_paused(self) -> bool:
        """Thread-safe check for pause state."""
        with QMutexLocker(self._mutex):
            return self._paused
    
    def request_cancel(self) -> None:
        """Request cancellation of the operation."""
        with QMutexLocker(self._mutex):
            self._cancelled = True
            self._paused = False  # Unpause to allow clean exit
        self.log("Cancellation requested", "warning")
    
    def pause(self) -> None:
        """Pause the operation."""
        with QMutexLocker(self._mutex):
            self._paused = True
        self.log("Operation paused", "info")
    
    def resume(self) -> None:
        """Resume a paused operation."""
        with QMutexLocker(self._mutex):
            self._paused = False
        self.log("Operation resumed", "info")
    
    def wait_if_paused(self) -> bool:
        """
        Block while paused. Returns False if cancelled during pause.
        
        Call this periodically in your do_work() implementation.
        """
        while self.is_paused:
            if self.is_cancelled:
                return False
            self.msleep(100)
        return not self.is_cancelled
    
    def report_progress(self, current: int, total: int, message: str = "") -> None:
        """Emit progress update."""
        self.progress.emit(current, total, message)
    
    def log(self, message: str, level: str = "info") -> None:
        """Emit log message."""
        self.log_message.emit(message, level)
        
        # Also log to Python logger
        log_func = getattr(logger, level, logger.info)
        log_func(message)
    
    def run(self) -> None:
        """Main thread entry point. Override do_work() instead."""
        try:
            self._result = self.do_work() or {}
            self.finished.emit(self._result)
        except Exception as e:
            logger.exception("Worker error: %s", e)
            self.error.emit(str(e))
            self.finished.emit({"error": str(e)})
    
    def do_work(self) -> Optional[Dict[str, Any]]:
        """
        Override this method to implement your task.
        
        Returns:
            Optional dict with results to pass to finished signal.
        """
        raise NotImplementedError("Subclasses must implement do_work()")


class AsyncTaskWorker(QThread):
    """
    Worker for running async/await coroutines in a Qt context.
    
    Useful for:
    - AppleScript execution (osascript)
    - Network operations with asyncio
    - Any async code that needs to run off the main thread
    
    Example:
        async def fetch_data():
            async with aiohttp.ClientSession() as session:
                return await session.get(url)
        
        worker = AsyncTaskWorker(fetch_data)
        worker.finished.connect(handle_result)
        worker.start()
    """
    
    finished = Signal(object)  # Result of the coroutine
    error = Signal(str)        # Error message
    
    def __init__(
        self,
        coro_func: Callable,
        *args,
        **kwargs
    ):
        super().__init__()
        self.coro_func = coro_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self) -> None:
        """Execute the coroutine in a new event loop."""
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.coro_func(*self.args, **self.kwargs)
            )
            self.finished.emit(result)
        except asyncio.CancelledError:
            self.error.emit("Operation cancelled")
        except Exception as e:
            logger.exception("Async worker error: %s", e)
            self.error.emit(str(e))
        finally:
            if loop and not loop.is_closed():
                loop.close()


class BatchWorker(BaseWorker):
    """
    Worker for processing items in batches with progress tracking.
    
    Provides batch processing with:
    - Configurable batch size
    - Per-item callbacks
    - Aggregate statistics
    
    Example:
        class FileProcessor(BatchWorker):
            def process_item(self, filepath):
                # Process single file
                return {"size": os.path.getsize(filepath)}
        
        worker = FileProcessor(file_list, batch_size=10)
        worker.start()
    """
    
    item_processed = Signal(object, object)  # item, result
    
    def __init__(
        self,
        items: List[Any],
        batch_size: int = 10,
        parent=None
    ):
        super().__init__(parent)
        self.items = items
        self.batch_size = batch_size
        self.stats = {
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }
    
    def do_work(self) -> Dict[str, Any]:
        """Process all items."""
        total = len(self.items)
        
        for i, item in enumerate(self.items):
            # Check for cancellation/pause
            if not self.wait_if_paused():
                break
            
            try:
                result = self.process_item(item)
                self.stats["succeeded"] += 1
                self.item_processed.emit(item, result)
            except Exception as e:
                self.stats["failed"] += 1
                self.log(f"Failed to process {item}: {e}", "error")
            
            self.stats["processed"] += 1
            self.report_progress(i + 1, total, str(item))
        
        return self.stats
    
    def process_item(self, item: Any) -> Any:
        """
        Override to process a single item.
        
        Args:
            item: The item to process.
            
        Returns:
            Result of processing (passed to item_processed signal).
        """
        raise NotImplementedError("Subclasses must implement process_item()")
