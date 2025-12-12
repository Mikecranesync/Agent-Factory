"""
Singleton pattern for Telegram bot using cross-platform file locking.

Prevents multiple bot instances from running simultaneously, which would cause
Telegram API conflicts ("terminated by other getUpdates request").

Uses filelock library for OS-level locking that survives crashes and works
across all process launch methods (manual, Task Scheduler, Windows Service, etc.).
"""

import os
import sys
from pathlib import Path
from typing import Optional
from filelock import FileLock, Timeout


class BotLockError(Exception):
    """Raised when bot lock cannot be acquired."""
    pass


class BotLock:
    """
    Cross-platform process lock for Telegram bot singleton.

    Ensures only ONE bot instance can run at a time by holding an OS-level
    file lock. The lock is automatically released when the process exits.

    Example:
        >>> with BotLock() as lock:
        ...     # Bot runs here
        ...     await bot.run()
        # Lock auto-released

    Attributes:
        lock_file: Path to lock file
        lock: FileLock instance
        timeout: Max seconds to wait for lock (default: 0 = immediate fail)
    """

    def __init__(
        self,
        lock_file: Optional[Path] = None,
        timeout: float = 0
    ):
        """
        Initialize bot lock.

        Args:
            lock_file: Path to lock file (default: .telegram_bot.lock in project root)
            timeout: Seconds to wait for lock (0 = fail immediately, -1 = wait forever)

        Example:
            >>> lock = BotLock()  # Uses default lock file
            >>> lock = BotLock(Path("/tmp/mybot.lock"), timeout=5)  # Custom lock, 5sec wait
        """
        if lock_file is None:
            # Default: .telegram_bot.lock in project root
            project_root = Path(__file__).parent.parent.parent.parent
            lock_file = project_root / ".telegram_bot.lock"

        self.lock_file = lock_file
        self.timeout = timeout
        self.lock = FileLock(str(lock_file), timeout=timeout)
        self._acquired = False

    def acquire(self):
        """
        Acquire the bot lock.

        Raises:
            BotLockError: If lock cannot be acquired (another instance is running)

        Example:
            >>> lock = BotLock()
            >>> lock.acquire()  # Raises BotLockError if bot already running
            >>> # ... run bot ...
            >>> lock.release()
        """
        try:
            self.lock.acquire(timeout=self.timeout)
            self._acquired = True
            print(f"✅ Bot lock acquired: {self.lock_file}")

        except Timeout:
            raise BotLockError(
                f"❌ Bot is already running!\n\n"
                f"Lock file exists: {self.lock_file}\n\n"
                f"If you're sure no bot is running:\n"
                f"  1. Check Task Manager for python.exe processes\n"
                f"  2. Check Windows Services for 'AgentFactoryTelegram'\n"
                f"  3. Manually delete: {self.lock_file}\n\n"
                f"To stop the running bot:\n"
                f"  python scripts/bot_manager.py stop"
            )

    def release(self):
        """
        Release the bot lock.

        Example:
            >>> lock = BotLock()
            >>> lock.acquire()
            >>> lock.release()  # Explicitly release
        """
        if self._acquired:
            try:
                self.lock.release()
                self._acquired = False
                print(f"✅ Bot lock released: {self.lock_file}")
            except Exception as e:
                print(f"⚠️ Warning: Failed to release lock: {e}")

    def is_locked(self) -> bool:
        """
        Check if lock file exists (another instance may be running).

        Returns:
            True if lock file exists, False otherwise

        Example:
            >>> lock = BotLock()
            >>> if lock.is_locked():
            ...     print("Bot is already running")
        """
        return self.lock_file.exists()

    def get_pid_from_lock(self) -> Optional[int]:
        """
        Try to read PID from lock file (if it contains PID info).

        Returns:
            PID of process holding lock, or None if unavailable

        Note:
            filelock doesn't store PID by default, so this may return None.
            For PID tracking, use the health check endpoint instead.
        """
        # filelock doesn't store PID in lock file
        # Use health check endpoint for PID info
        return None

    def __enter__(self):
        """
        Context manager entry - acquire lock.

        Example:
            >>> with BotLock() as lock:
            ...     # Bot runs here
            ...     pass
        """
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit - release lock.

        Lock is released even if exception occurs inside context.
        """
        self.release()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Destructor - ensure lock is released."""
        if self._acquired:
            self.release()


def check_bot_running() -> bool:
    """
    Check if bot is currently running.

    Returns:
        True if bot is running (lock file exists), False otherwise

    Example:
        >>> from agent_factory.integrations.telegram.singleton import check_bot_running
        >>> if check_bot_running():
        ...     print("Bot is running!")
    """
    lock = BotLock()
    return lock.is_locked()


def force_release_lock():
    """
    Force release bot lock by deleting lock file.

    WARNING: Only use this if you're certain no bot is running.
    If bot IS running, it will cause instance conflicts.

    Example:
        >>> from agent_factory.integrations.telegram.singleton import force_release_lock
        >>> force_release_lock()  # Emergency unlock
    """
    lock = BotLock()
    if lock.lock_file.exists():
        try:
            lock.lock_file.unlink()
            print(f"✅ Forcefully removed lock file: {lock.lock_file}")
        except Exception as e:
            print(f"❌ Failed to remove lock file: {e}")
    else:
        print(f"ℹ️ No lock file found: {lock.lock_file}")
