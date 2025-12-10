"""
Settings Service - Database-backed configuration with environment fallback

Pattern from Archon's CredentialService (13.4k⭐ production system).

Enables runtime configuration changes without code changes or service restarts.
All major features can be toggled via database settings.

Usage:
    from agent_factory.core.settings_service import settings

    # Get setting (falls back to env var if not in database)
    model = settings.get("DEFAULT_MODEL", category="llm")

    # Get typed settings
    batch_size = settings.get_int("BATCH_SIZE", default=50, category="memory")
    use_hybrid = settings.get_bool("USE_HYBRID_SEARCH", category="memory")

    # Reload settings from database (optional - cache is auto-populated)
    settings.reload()
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class SettingsService:
    """
    Database-backed settings with environment variable fallback.

    Features:
    - In-memory cache for fast lookups
    - Automatic fallback to environment variables
    - Type conversion helpers (bool, int, float)
    - TTL-based cache expiration (5 minutes)
    - Graceful degradation if database unavailable
    """

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize Settings Service.

        Args:
            supabase_url: Supabase project URL (or use SUPABASE_URL env var)
            supabase_key: Supabase anon/service key (or use SUPABASE_KEY env var)
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        self.client: Optional[Any] = None
        self._cache: Dict[str, str] = {}
        self._cache_initialized = False
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(minutes=5)  # Cache expires after 5 minutes

        # Try to initialize Supabase client
        if self.supabase_url and self.supabase_key:
            try:
                from supabase import create_client
                self.client = create_client(self.supabase_url, self.supabase_key)
                self._load_cache()
            except ImportError:
                print("[WARN] supabase package not installed - using environment variables only")
                self.client = None
            except Exception as e:
                print(f"[WARN] Failed to connect to Supabase for settings: {e}")
                print("[INFO] Settings service will use environment variables only")
                self.client = None
        else:
            print("[INFO] Settings service using environment variables only (no Supabase credentials)")

    def _is_cache_expired(self) -> bool:
        """Check if cache has expired based on TTL"""
        if not self._cache_timestamp:
            return True
        return datetime.now() - self._cache_timestamp > self._cache_ttl

    def _load_cache(self):
        """Load all settings from database into memory cache"""
        if not self.client:
            return

        try:
            response = self.client.table("agent_factory_settings").select("*").execute()

            # Clear existing cache
            self._cache.clear()

            # Populate cache with category.key format
            for row in response.data:
                cache_key = f"{row['category']}.{row['key']}"
                self._cache[cache_key] = row['value']

            self._cache_initialized = True
            self._cache_timestamp = datetime.now()

            print(f"[OK] Settings cache loaded: {len(self._cache)} settings from database")

        except Exception as e:
            print(f"[WARN] Failed to load settings from database: {e}")
            print("[INFO] Falling back to environment variables")
            self._cache_initialized = False

    def reload(self):
        """
        Reload settings from database.

        Useful for picking up runtime configuration changes.
        Call this after updating settings via Supabase UI or API.
        """
        if not self.client:
            print("[INFO] No database connection - cannot reload settings")
            return

        print("[INFO] Reloading settings from database...")
        self._load_cache()

    def get(self, key: str, default: str = "", category: str = "general") -> str:
        """
        Get a setting value.

        Lookup order:
        1. Database cache (if initialized and not expired)
        2. Environment variable
        3. Default value

        Args:
            key: Setting key (e.g., "DEFAULT_MODEL")
            default: Default value if not found
            category: Setting category (e.g., "llm", "memory", "orchestration")

        Returns:
            Setting value as string

        Example:
            >>> settings.get("DEFAULT_MODEL", category="llm")
            'gpt-4o-mini'

            >>> settings.get("BATCH_SIZE", default="50", category="memory")
            '50'
        """
        cache_key = f"{category}.{key}"

        # Check if cache needs refresh
        if self._cache_initialized and self._is_cache_expired():
            print("[INFO] Settings cache expired - reloading...")
            self._load_cache()

        # Try cache first (if initialized)
        if self._cache_initialized and cache_key in self._cache:
            return self._cache[cache_key]

        # Fall back to environment variable
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value

        # Return default
        return default

    def get_bool(self, key: str, default: bool = False, category: str = "general") -> bool:
        """
        Get a boolean setting.

        Recognizes: "true", "1", "yes", "on" as True (case-insensitive)
        Everything else is False

        Args:
            key: Setting key
            default: Default value if not found
            category: Setting category

        Returns:
            Boolean value

        Example:
            >>> settings.get_bool("USE_HYBRID_SEARCH", category="memory")
            False

            >>> settings.get_bool("DEBUG_MODE", default=True, category="general")
            True
        """
        value = self.get(key, "false" if not default else "true", category)
        return value.lower() in ("true", "1", "yes", "on")

    def get_int(self, key: str, default: int = 0, category: str = "general") -> int:
        """
        Get an integer setting.

        Args:
            key: Setting key
            default: Default value if not found or invalid
            category: Setting category

        Returns:
            Integer value

        Example:
            >>> settings.get_int("BATCH_SIZE", default=50, category="memory")
            50

            >>> settings.get_int("MAX_RETRIES", category="orchestration")
            3
        """
        value = self.get(key, str(default), category)
        try:
            return int(value)
        except ValueError:
            print(f"[WARN] Invalid integer value for {category}.{key}: '{value}' - using default {default}")
            return default

    def get_float(self, key: str, default: float = 0.0, category: str = "general") -> float:
        """
        Get a float setting.

        Args:
            key: Setting key
            default: Default value if not found or invalid
            category: Setting category

        Returns:
            Float value

        Example:
            >>> settings.get_float("DEFAULT_TEMPERATURE", default=0.7, category="llm")
            0.7
        """
        value = self.get(key, str(default), category)
        try:
            return float(value)
        except ValueError:
            print(f"[WARN] Invalid float value for {category}.{key}: '{value}' - using default {default}")
            return default

    def set(self, key: str, value: str, category: str = "general", description: str = "") -> bool:
        """
        Set a setting value in the database.

        Args:
            key: Setting key
            value: Setting value (will be converted to string)
            category: Setting category
            description: Optional description of the setting

        Returns:
            True if successful, False otherwise

        Example:
            >>> settings.set("BATCH_SIZE", "100", category="memory", description="Batch size for memory operations")
            True

            >>> settings.set("DEBUG_MODE", "true", category="general")
            True
        """
        if not self.client:
            print("[ERROR] Cannot set value - no database connection")
            return False

        try:
            # Use upsert to insert or update
            self.client.table("agent_factory_settings").upsert({
                "category": category,
                "key": key,
                "value": str(value),
                "description": description,
                "updated_at": datetime.now().isoformat()
            }).execute()

            # Update cache
            cache_key = f"{category}.{key}"
            self._cache[cache_key] = str(value)

            print(f"[OK] Setting updated: {category}.{key} = {value}")
            return True

        except Exception as e:
            print(f"[ERROR] Failed to set {category}.{key}: {e}")
            return False

    def get_all(self, category: Optional[str] = None) -> Dict[str, str]:
        """
        Get all settings, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            Dictionary of key -> value mappings

        Example:
            >>> settings.get_all(category="llm")
            {'DEFAULT_MODEL': 'gpt-4o-mini', 'DEFAULT_TEMPERATURE': '0.7'}

            >>> settings.get_all()
            {'llm.DEFAULT_MODEL': 'gpt-4o-mini', 'memory.BATCH_SIZE': '50', ...}
        """
        if not self._cache_initialized:
            return {}

        if category:
            prefix = f"{category}."
            return {
                key.replace(prefix, ""): value
                for key, value in self._cache.items()
                if key.startswith(prefix)
            }
        else:
            return self._cache.copy()

    def __repr__(self) -> str:
        """String representation of settings service"""
        status = "connected" if self.client else "environment-only"
        cache_size = len(self._cache) if self._cache_initialized else 0
        return f"<SettingsService status={status} cached_settings={cache_size}>"


# Singleton instance - import and use this
settings = SettingsService()
