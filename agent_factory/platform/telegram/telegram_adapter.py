"""
Telegram Adapter for Factory.io Platform

Bridges MachineStateManager with Telegram chat interfaces, providing
real-time I/O monitoring and control buttons for Factory.io machines.

Architecture:
    Factory.io → MachineStateManager → TelegramAdapter → Telegram Chat
                                       ↑                    ↓
                                       └──── button clicks ──┘

Usage:
    from agent_factory.platform.telegram import TelegramAdapter
    from telegram import Bot

    # Initialize
    bot = Bot(token="YOUR_BOT_TOKEN")
    adapter = TelegramAdapter(state_manager, bot, machine_config, readwrite_tool)

    # Start (subscribe to state changes)
    await adapter.start()

    # Stop (unsubscribe)
    await adapter.stop()
"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from telegram.error import TelegramError, Forbidden, BadRequest

from agent_factory.platform.config import MachineConfig, MachineConfigList
from agent_factory.platform.state.machine_state_manager import MachineStateManager
from agent_factory.platform.types import IOTagStatus, ControlButton, PlatformMessage, AlertMessage
from agent_factory.tools.factoryio.readwrite_tool import FactoryIOReadWriteTool
from agent_factory.integrations.telegram.formatters import ResponseFormatter

logger = logging.getLogger(__name__)


# ============================================================================
# Force Provider (PLC HMI-style Force Controls)
# ============================================================================


class ForceProvider:
    """
    Manages forced tag values for PLC HMI-style force controls.

    Forces are stored in-memory and cleared on restart (safety feature).
    All force operations are logged for audit trail.

    Usage:
        provider = ForceProvider()
        provider.set_force("machine1", "conveyor", True, "user123")
        is_forced = provider.is_forced("machine1", "conveyor")
        provider.clear_force("machine1", "conveyor", "user123")

    Attributes:
        _forced_tags: Dict mapping machine_id → {tag_name: forced_value}
        _force_log: Audit log of all force operations
    """

    def __init__(self):
        """Initialize ForceProvider with empty state."""
        self._forced_tags: Dict[str, Dict[str, bool]] = {}  # machine_id → {tag_name: value}
        self._force_log: List[Dict] = []  # Audit log

    def set_force(self, machine_id: str, tag_name: str, value: bool, user: str) -> None:
        """
        Set a tag to forced value.

        Args:
            machine_id: ID of machine containing the tag
            tag_name: Name of tag to force
            value: Value to force (True/False)
            user: Username or ID of user who set the force

        Example:
            provider.set_force("scene1_sorting", "conveyor_running", True, "john_doe")
        """
        if machine_id not in self._forced_tags:
            self._forced_tags[machine_id] = {}
        self._forced_tags[machine_id][tag_name] = value

        # Audit log
        log_entry = {
            "timestamp": datetime.now(),
            "machine_id": machine_id,
            "tag_name": tag_name,
            "value": value,
            "user": user,
            "action": "set_force"
        }
        self._force_log.append(log_entry)
        logger.warning(f"FORCE: {user} forced {machine_id}.{tag_name} = {value}")

    def clear_force(self, machine_id: str, tag_name: str, user: str) -> None:
        """
        Remove force from a tag (return to normal operation).

        Args:
            machine_id: ID of machine containing the tag
            tag_name: Name of tag to clear force from
            user: Username or ID of user who cleared the force

        Example:
            provider.clear_force("scene1_sorting", "conveyor_running", "john_doe")
        """
        if machine_id in self._forced_tags and tag_name in self._forced_tags[machine_id]:
            del self._forced_tags[machine_id][tag_name]

            # Audit log
            log_entry = {
                "timestamp": datetime.now(),
                "machine_id": machine_id,
                "tag_name": tag_name,
                "user": user,
                "action": "clear_force"
            }
            self._force_log.append(log_entry)
            logger.info(f"CLEAR FORCE: {user} cleared force on {machine_id}.{tag_name}")

    def get_forced_value(self, machine_id: str, tag_name: str) -> Optional[bool]:
        """
        Get forced value if tag is forced, else None.

        Args:
            machine_id: ID of machine containing the tag
            tag_name: Name of tag to check

        Returns:
            Forced value (True/False) if forced, None if not forced

        Example:
            value = provider.get_forced_value("scene1_sorting", "conveyor_running")
            if value is not None:
                print(f"Tag is forced to {value}")
        """
        return self._forced_tags.get(machine_id, {}).get(tag_name)

    def is_forced(self, machine_id: str, tag_name: str) -> bool:
        """
        Check if a tag is currently forced.

        Args:
            machine_id: ID of machine containing the tag
            tag_name: Name of tag to check

        Returns:
            True if tag is forced, False otherwise

        Example:
            if provider.is_forced("scene1_sorting", "conveyor_running"):
                print("Conveyor is under force control")
        """
        return tag_name in self._forced_tags.get(machine_id, {})

    def get_all_forced(self, machine_id: str) -> Dict[str, bool]:
        """
        Get all forced tags for a machine.

        Args:
            machine_id: ID of machine

        Returns:
            Dict of {tag_name: forced_value} for all forced tags

        Example:
            forced_tags = provider.get_all_forced("scene1_sorting")
            for tag, value in forced_tags.items():
                print(f"{tag} forced to {value}")
        """
        return self._forced_tags.get(machine_id, {}).copy()

    def get_force_log(self, machine_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Get force audit log.

        Args:
            machine_id: Optional filter by machine ID
            limit: Maximum number of entries to return (default: 100)

        Returns:
            List of log entries (most recent first)

        Example:
            log = provider.get_force_log("scene1_sorting", limit=10)
            for entry in log:
                print(f"{entry['timestamp']}: {entry['user']} {entry['action']} {entry['tag_name']}")
        """
        if machine_id:
            filtered = [entry for entry in self._force_log if entry.get("machine_id") == machine_id]
        else:
            filtered = self._force_log

        # Return most recent first
        return list(reversed(filtered[-limit:]))


# ============================================================================
# Message Tracking
# ============================================================================


@dataclass
class MessageTracker:
    """
    Tracks message IDs per chat for editing vs sending new messages.

    Hybrid strategy:
    - Edit message if last update was < edit_threshold_seconds ago
    - Send new message if last update was > edit_threshold_seconds ago

    Attributes:
        machine_id: ID of machine this tracker belongs to
        chat_id: Telegram chat ID
        message_id: Last message ID sent to this chat (None if no message sent)
        last_sent_at: Timestamp of last message send/edit
        edit_threshold_seconds: Threshold for edit vs send new (default: 5s)
    """
    machine_id: str
    chat_id: int
    message_id: Optional[int] = None
    last_sent_at: Optional[datetime] = None
    edit_threshold_seconds: int = 3600  # 1 hour (effectively always edit for Factory.io HMI)

    def should_edit(self) -> bool:
        """
        Check if we should edit the existing message or send a new one.

        Returns:
            True if should edit (message exists and sent recently)
        """
        if self.message_id is None or self.last_sent_at is None:
            return False

        elapsed = (datetime.now() - self.last_sent_at).total_seconds()
        return elapsed < self.edit_threshold_seconds


# ============================================================================
# Telegram Adapter (Main Class)
# ============================================================================


class TelegramAdapter:
    """
    Telegram adapter for Factory.io real-time monitoring and control.

    Subscribes to MachineStateManager state changes and sends formatted
    messages with inline keyboard controls to Telegram chats.

    Attributes:
        state_manager: MachineStateManager instance for state subscription
        bot: Telegram Bot instance for sending messages
        machine_config: Machine configuration list
        readwrite_tool: FactoryIOReadWriteTool for executing writes
        executor: ThreadPoolExecutor for sync I/O operations
        subscriptions: Dict of machine_id → subscription_id
        message_trackers: Dict of machine_id → MessageTracker
        last_write_time: Dict of chat_id → datetime for rate limiting
        write_cooldown_seconds: Minimum time between writes (rate limiting)
    """

    def __init__(
        self,
        state_manager: MachineStateManager,
        bot: Bot,
        machine_config: MachineConfigList,
        readwrite_tool: Optional[FactoryIOReadWriteTool] = None,
        write_cooldown_seconds: int = 1,
        executor: Optional[ThreadPoolExecutor] = None
    ):
        """
        Initialize TelegramAdapter.

        Args:
            state_manager: MachineStateManager instance for state subscription
            bot: Telegram Bot instance for sending messages
            machine_config: Machine configuration list
            readwrite_tool: FactoryIOReadWriteTool for executing writes (default: creates new instance)
            write_cooldown_seconds: Minimum time between writes per chat (default: 1s)
            executor: ThreadPoolExecutor for sync operations (default: creates 4-worker pool)
        """
        self.state_manager = state_manager
        self.bot = bot
        self.machine_config = machine_config
        self.readwrite_tool = readwrite_tool or FactoryIOReadWriteTool()
        self.write_cooldown_seconds = write_cooldown_seconds
        self.executor = executor or ThreadPoolExecutor(max_workers=4, thread_name_prefix="telegram-adapter")

        # Internal state
        self.subscriptions: Dict[str, str] = {}  # machine_id → subscription_id
        self.message_trackers: Dict[str, MessageTracker] = {}  # machine_id → MessageTracker
        self.last_write_time: Dict[int, datetime] = {}  # chat_id → datetime
        self.force_provider = ForceProvider()  # PLC HMI-style force controls
        self._running = False

        logger.info("TelegramAdapter initialized with %d machines", len(machine_config.machines))

    async def start(self) -> None:
        """
        Start the adapter by subscribing to all machine state changes.

        Subscribes to MachineStateManager for each configured machine.
        """
        if self._running:
            logger.warning("TelegramAdapter already running")
            return

        logger.info("Starting TelegramAdapter...")
        self._running = True

        # Subscribe to state changes for each machine
        for machine in self.machine_config.machines:
            subscription_id = self.state_manager.subscribe(
                machine_id=machine.machine_id,
                callback=self._on_state_change
            )
            self.subscriptions[machine.machine_id] = subscription_id
            logger.info(f"Subscribed to {machine.machine_id} (sub_id: {subscription_id})")

        logger.info(f"TelegramAdapter started with {len(self.subscriptions)} subscriptions")

    async def stop(self) -> None:
        """
        Stop the adapter by unsubscribing from all state changes.

        Unsubscribes from MachineStateManager and cleans up resources.
        """
        if not self._running:
            logger.warning("TelegramAdapter not running")
            return

        logger.info("Stopping TelegramAdapter...")
        self._running = False

        # Unsubscribe from all machines
        for machine_id, subscription_id in self.subscriptions.items():
            self.state_manager.unsubscribe(subscription_id)
            logger.info(f"Unsubscribed from {machine_id} (sub_id: {subscription_id})")

        self.subscriptions.clear()
        logger.info("TelegramAdapter stopped")

    # ========================================================================
    # State Change Callback (Subscription)
    # ========================================================================

    async def _on_state_change(self, machine_id: str, changed_tags: List[IOTagStatus]) -> None:
        """
        Callback invoked when machine state changes.

        Builds PlatformMessage from state and sends to Telegram.

        Args:
            machine_id: ID of machine that changed
            changed_tags: List of tags that changed
        """
        try:
            # Get machine configuration
            machine = self.machine_config.get_machine(machine_id)
            if not machine:
                logger.error(f"Machine {machine_id} not found in config")
                return

            # Log state change
            logger.debug(f"State change for {machine_id}: {len(changed_tags)} tags changed")

            # Apply forced values (PLC HMI force controls)
            forced_tags = self.force_provider.get_all_forced(machine_id)
            if forced_tags:
                logger.debug(f"Applying {len(forced_tags)} forced tag(s) for {machine_id}")
                for tag_name, forced_value in forced_tags.items():
                    try:
                        await self._write_tag_async(machine_id, tag_name, forced_value)
                    except Exception as e:
                        logger.error(f"Failed to apply force to {tag_name}: {e}")

            # Format message
            text, keyboard = self._format_message(machine_id)

            # Send or edit message
            await self._send_or_edit_message(
                chat_id=machine.telegram_chat_id,
                text=text,
                keyboard=keyboard,
                machine_id=machine_id
            )

        except Exception as e:
            logger.error(f"Error handling state change for {machine_id}: {e}", exc_info=True)

    # ========================================================================
    # Message Formatting
    # ========================================================================

    def _format_message(self, machine_id: str) -> Tuple[str, InlineKeyboardMarkup]:
        """
        Format machine state as Telegram message with inline keyboard.

        Args:
            machine_id: ID of machine to format

        Returns:
            Tuple of (message_text, inline_keyboard_markup)
        """
        # Get machine configuration
        machine = self.machine_config.get_machine(machine_id)
        if not machine:
            raise ValueError(f"Machine {machine_id} not found in config")

        # Get current state from state manager
        state = self.state_manager.get_state(machine_id)
        is_healthy = self.state_manager.is_healthy(machine_id)

        # Build PlatformMessage
        message = PlatformMessage(
            title=machine.scene_name,
            description=f"Machine ID: {machine_id}"
        )

        # Add I/O tags from state
        for tag_name, tag in state.items():
            message.add_io_tag(tag)

        # Add controls (only if healthy)
        if is_healthy:
            # Add controllable output buttons
            for output in machine.controllable_outputs:
                if output.tag not in machine.read_only_tags:
                    current_value = state.get(output.tag)
                    button = ControlButton(
                        label=output.label,
                        tag_name=output.tag,
                        action="toggle",
                        emoji=output.emoji or "🔘"
                    )
                    message.add_control(button)

            # Add emergency stop button
            if machine.emergency_stop_tags:
                emergency_button = ControlButton(
                    label="EMERGENCY STOP",
                    tag_name="",
                    action="emergency_stop",
                    emoji="🚨",
                    style="danger"
                )
                message.add_control(emergency_button)

        # Convert to Telegram format
        text = self._to_markdown(message, machine_id)
        keyboard = self._to_keyboard(message, machine_id)

        return (text, keyboard)

    def _to_markdown(self, message: PlatformMessage, machine_id: str) -> str:
        """
        Convert PlatformMessage to PLC HMI-style Telegram Markdown V2 format.

        PLC HMI Format:
            🟢 tag_name (Human-readable comment)          [Force buttons]
            ⚫ tag_name (Human-readable comment) ⚠️ FORCED [Force buttons]

        Args:
            message: PlatformMessage to convert
            machine_id: ID of machine (for health status and force checking)

        Returns:
            Markdown-formatted message text in PLC HMI style
        """
        # Get health status
        health_info = self.state_manager.get_health_status().get(machine_id, {})
        circuit_state = health_info.get("circuit_state", "closed")

        # Determine status text
        if circuit_state == "closed":
            status_text = "🟢 ONLINE"
        elif circuit_state == "half_open":
            status_text = "🟡 TESTING"
        else:  # open
            status_text = "🔴 OFFLINE"

        # Get machine config for tag comments
        machine = self.machine_config.get_machine(machine_id)

        # Build message parts
        parts = []

        # Header with status
        title = ResponseFormatter.escape_markdown(message.title.upper())
        status_part = ResponseFormatter.escape_markdown(f"({status_text})")
        parts.append(f"*{title}* {status_part}")
        parts.append("")  # Blank line

        # I/O Status - INPUTS (PLC HMI style)
        inputs = message.get_inputs()
        if inputs:
            parts.append("📥 *INPUTS:*")
            # Sort alphabetically
            for tag_name in sorted(inputs.keys()):
                tag = inputs[tag_name]

                # Status indicator (🟢 = HIGH/TRUE, ⚫ = LOW/FALSE)
                status_indicator = "🟢" if tag.value else "⚫"

                # Get comment from config
                comment = self._get_tag_comment(machine, tag_name) if machine else None
                if comment:
                    tag_display = f"{tag_name} ({comment})"
                else:
                    tag_display = tag_name
                tag_display = ResponseFormatter.escape_markdown(tag_display)

                # Check if forced
                force_indicator = " ⚠️ *FORCED*" if self.force_provider.is_forced(machine_id, tag_name) else ""

                parts.append(f"{status_indicator} {tag_display}{force_indicator}")
            parts.append("")

        # I/O Status - OUTPUTS (PLC HMI style)
        outputs = message.get_outputs()
        if outputs:
            parts.append("📤 *OUTPUTS:*")
            # Sort alphabetically
            for tag_name in sorted(outputs.keys()):
                tag = outputs[tag_name]

                # Status indicator (🟢 = HIGH/TRUE, ⚫ = LOW/FALSE)
                status_indicator = "🟢" if tag.value else "⚫"

                # Get comment from config
                comment = self._get_tag_comment(machine, tag_name) if machine else None
                if comment:
                    tag_display = f"{tag_name} ({comment})"
                else:
                    tag_display = tag_name
                tag_display = ResponseFormatter.escape_markdown(tag_display)

                # Check if forced
                force_indicator = " ⚠️ *FORCED*" if self.force_provider.is_forced(machine_id, tag_name) else ""

                parts.append(f"{status_indicator} {tag_display}{force_indicator}")
            parts.append("")

        # Alerts
        if message.alerts:
            parts.append("⚠️ *ALERTS:*")
            for alert in message.alerts:
                level_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(alert.level, "ℹ️")
                alert_text = ResponseFormatter.escape_markdown(alert.text)
                parts.append(f"{level_emoji} {alert_text}")
            parts.append("")

        # Last update time
        now = datetime.now().strftime("%H:%M:%S")
        parts.append(f"_Last update: {now}_")

        return "\n".join(parts)

    def _to_keyboard(self, message: PlatformMessage, machine_id: str) -> InlineKeyboardMarkup:
        """
        Generate PLC HMI-style force control buttons for outputs.

        Layout:
            [ON] [OFF] [Clear]  ← One row per output tag
            [ON] [OFF] [Clear]
            [⛔ EMERGENCY STOP]  ← Separate row
            [🔄 Refresh]         ← Separate row

        Args:
            message: PlatformMessage with I/O status
            machine_id: ID of machine (for callback data)

        Returns:
            InlineKeyboardMarkup with force control buttons
        """
        keyboard = []

        # Get machine config
        machine = self.machine_config.get_machine(machine_id)
        if not machine:
            return InlineKeyboardMarkup([])

        # Get outputs (sorted alphabetically to match message display)
        outputs = sorted(message.get_outputs().items())

        # Create force control buttons for each output
        for tag_name, tag in outputs:
            # Skip read-only tags
            if tag_name in machine.read_only_tags:
                continue

            # One row per output: [ON] [OFF] [Clear]
            row = [
                InlineKeyboardButton(
                    "ON",
                    callback_data=f"force:{machine_id}:{tag_name}:1"
                ),
                InlineKeyboardButton(
                    "OFF",
                    callback_data=f"force:{machine_id}:{tag_name}:0"
                ),
                InlineKeyboardButton(
                    "Clear",
                    callback_data=f"clear:{machine_id}:{tag_name}"
                )
            ]
            keyboard.append(row)

        # Add emergency stop button (separate row, full width)
        if machine.emergency_stop_tags:
            keyboard.append([
                InlineKeyboardButton(
                    "⛔ EMERGENCY STOP",
                    callback_data=f"estop:{machine_id}"
                )
            ])

        # Add refresh button (separate row, full width)
        keyboard.append([
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data=f"refresh:{machine_id}"
            )
        ])

        return InlineKeyboardMarkup(keyboard)

    # ========================================================================
    # Message Sending
    # ========================================================================

    async def _send_or_edit_message(
        self,
        chat_id: int,
        text: str,
        keyboard: InlineKeyboardMarkup,
        machine_id: str
    ) -> None:
        """
        Send new message or edit existing message (hybrid strategy).

        Args:
            chat_id: Telegram chat ID
            text: Message text (Markdown V2)
            keyboard: Inline keyboard markup
            machine_id: Machine ID (for tracking)
        """
        tracker = self._get_tracker(machine_id)

        try:
            if tracker.should_edit():
                # Edit existing message
                try:
                    await self.bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=tracker.message_id,
                        text=text,
                        parse_mode=ParseMode.MARKDOWN_V2,
                        reply_markup=keyboard
                    )
                    tracker.last_sent_at = datetime.now()
                    logger.debug(f"Edited message {tracker.message_id} in chat {chat_id}")
                except BadRequest as e:
                    if "not modified" in str(e).lower():
                        # Message content unchanged, ignore
                        logger.debug(f"Message {tracker.message_id} not modified, skipping edit")
                    else:
                        # Other error, send new message instead
                        logger.warning(f"Failed to edit message: {e}. Sending new message.")
                        tracker.message_id = None  # Reset to trigger send
                        await self._send_or_edit_message(chat_id, text, keyboard, machine_id)
            else:
                # Send new message
                message = await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.MARKDOWN_V2,
                    reply_markup=keyboard
                )
                tracker.message_id = message.message_id
                tracker.last_sent_at = datetime.now()
                logger.debug(f"Sent new message {message.message_id} to chat {chat_id}")

        except Forbidden as e:
            # Bot blocked by user, remove tracker
            logger.warning(f"Bot blocked by chat {chat_id}, removing tracker: {e}")
            if machine_id in self.message_trackers:
                del self.message_trackers[machine_id]
        except TelegramError as e:
            logger.error(f"Telegram error sending/editing message to chat {chat_id}: {e}")

    async def _send_alert(self, chat_id: int, alert: AlertMessage) -> None:
        """
        Send alert message to chat.

        Args:
            chat_id: Telegram chat ID
            alert: Alert message to send
        """
        # Determine emoji based on level
        level_emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🔴"}.get(alert.level, "ℹ️")

        # Format alert text
        alert_text = ResponseFormatter.escape_markdown(alert.text)
        text = f"{level_emoji} *ALERT*\n\n{alert_text}"

        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=ParseMode.MARKDOWN_V2
            )

            # Pin critical alerts
            if alert.level == "error":
                try:
                    await self.bot.pin_chat_message(
                        chat_id=chat_id,
                        message_id=message.message_id,
                        disable_notification=False
                    )
                    logger.info(f"Pinned critical alert in chat {chat_id}")
                except TelegramError as e:
                    logger.warning(f"Failed to pin alert message: {e}")

        except Forbidden as e:
            logger.warning(f"Bot blocked by chat {chat_id}: {e}")
        except TelegramError as e:
            logger.error(f"Failed to send alert to chat {chat_id}: {e}")

    # ========================================================================
    # Callback Handling (Button Clicks)
    # ========================================================================
    # NOTE: handle_callback() is defined later at line ~1110 to match button format

    def _validate_callback_data(self, callback_data: str) -> Optional[dict]:
        """
        Validate and parse callback data from button click.

        Format: factoryio:action:machine_id:tag_name:value

        Args:
            callback_data: Callback data string from button

        Returns:
            Dict with parsed data if valid, None if invalid
        """
        # Check prefix
        if not callback_data.startswith("factoryio:"):
            logger.warning(f"Invalid callback_data prefix: {callback_data}")
            return None

        # Remove prefix and parse
        data = callback_data[10:]  # Remove "factoryio:"
        parts = data.split(":")

        if len(parts) < 3:
            logger.warning(f"Invalid callback_data format: {callback_data}")
            return None

        action = parts[0]
        machine_id = parts[1]
        tag_name = parts[2]
        value = parts[3] if len(parts) > 3 else None

        # Validate machine exists
        machine = self.machine_config.get_machine(machine_id)
        if not machine:
            logger.warning(f"Machine {machine_id} not found in config")
            return None

        # Validate action
        if action not in ["toggle", "write", "emergency_stop"]:
            logger.warning(f"Invalid action: {action}")
            return None

        # Validate tag (if not emergency stop)
        if action != "emergency_stop":
            if not tag_name:
                logger.warning(f"Missing tag_name for action {action}")
                return None

            # Check if tag is controllable
            controllable_tags = [t.tag for t in machine.controllable_outputs]
            if tag_name not in controllable_tags:
                logger.warning(f"Tag {tag_name} not controllable for machine {machine_id}")
                return None

            # Check if tag is read-only
            if tag_name in machine.read_only_tags:
                logger.warning(f"Tag {tag_name} is read-only")
                return None

        return {
            "action": action,
            "machine_id": machine_id,
            "tag_name": tag_name,
            "value": value
        }

    async def _execute_write(
        self,
        machine_id: str,
        tag_name: str,
        value: any
    ) -> Tuple[bool, str]:
        """
        Execute tag write to Factory.io.

        Args:
            machine_id: Machine ID (for URL lookup)
            tag_name: Tag name to write
            value: Value to write

        Returns:
            Tuple of (success, message)
        """
        machine = self.machine_config.get_machine(machine_id)
        if not machine:
            return (False, f"Machine {machine_id} not found")

        try:
            # Execute write in thread pool (FactoryIOReadWriteTool is synchronous)
            loop = asyncio.get_event_loop()
            result_json = await loop.run_in_executor(
                self.executor,
                self.readwrite_tool._run,
                "write",
                None,
                {tag_name: value}
            )

            # Parse result
            result = json.loads(result_json)

            if result.get("success"):
                return (True, f"✅ {tag_name} set to {value}")
            else:
                errors = result.get("errors", ["Unknown error"])
                return (False, f"❌ Failed: {errors[0]}")

        except Exception as e:
            logger.error(f"Error executing write for {machine_id}.{tag_name}: {e}", exc_info=True)
            return (False, f"❌ Error: {str(e)}")

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _get_tracker(self, machine_id: str) -> MessageTracker:
        """
        Get or create MessageTracker for machine.

        Args:
            machine_id: Machine ID

        Returns:
            MessageTracker instance
        """
        if machine_id not in self.message_trackers:
            machine = self.machine_config.get_machine(machine_id)
            if not machine:
                raise ValueError(f"Machine {machine_id} not found in config")

            self.message_trackers[machine_id] = MessageTracker(
                machine_id=machine_id,
                chat_id=machine.telegram_chat_id
            )

        return self.message_trackers[machine_id]

    def _check_rate_limit(self, chat_id: int) -> bool:
        """
        Check if write is allowed (rate limiting).

        Args:
            chat_id: Telegram chat ID

        Returns:
            True if write is allowed, False if rate limited
        """
        if chat_id not in self.last_write_time:
            return True

        elapsed = (datetime.now() - self.last_write_time[chat_id]).total_seconds()
        return elapsed >= self.write_cooldown_seconds

    def _update_write_time(self, chat_id: int) -> None:
        """
        Update last write time for rate limiting.

        Args:
            chat_id: Telegram chat ID
        """
        self.last_write_time[chat_id] = datetime.now()

    async def _write_tag_async(self, machine_id: str, tag_name: str, value: bool) -> None:
        """
        Force tag value in Factory.io (async wrapper for sync readwrite_tool).

        Uses Factory.io native force API to hold output at specific value.
        Critical for HMI manual control when no PLC logic is running.

        Args:
            machine_id: ID of machine containing the tag
            tag_name: Name of tag to force
            value: Value to force (True/False)

        Raises:
            Exception: If force fails
        """
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            lambda: self.readwrite_tool._run("force", tag_values={tag_name: value})
        )

        # Check for errors
        if "ERROR" in result:
            logger.error(f"Failed to force {machine_id}.{tag_name} = {value}: {result}")
            raise Exception(f"Factory.io write failed: {result}")
        else:
            logger.info(f"Wrote {machine_id}.{tag_name} = {value}")

    def _get_tag_comment(self, machine: MachineConfig, tag_name: str) -> Optional[str]:
        """
        Get human-readable comment for a tag from config.

        Args:
            machine: Machine configuration
            tag_name: Name of tag to look up

        Returns:
            Comment string if found, None otherwise

        Example:
            comment = self._get_tag_comment(machine, "conveyor_running")
            # Returns: "Main Conveyor Motor"
        """
        # Check monitored_inputs
        for tag_config in machine.monitored_inputs:
            if tag_config.tag == tag_name:
                return tag_config.comment if hasattr(tag_config, 'comment') else tag_config.label

        # Check controllable_outputs
        for tag_config in machine.controllable_outputs:
            if tag_config.tag == tag_name:
                return tag_config.comment if hasattr(tag_config, 'comment') else tag_config.label

        return None

    async def _send_or_edit_message_for_machine(self, machine_id: str) -> None:
        """
        Send/edit message for a specific machine (for manual refresh or button clicks).

        Args:
            machine_id: ID of machine to update

        Raises:
            ValueError: If machine not found in config
        """
        machine = self.machine_config.get_machine(machine_id)
        if not machine:
            raise ValueError(f"Machine {machine_id} not found in config")

        # Format message
        text, keyboard = self._format_message(machine_id)

        # Send or edit
        await self._send_or_edit_message(
            chat_id=machine.telegram_chat_id,
            text=text,
            keyboard=keyboard,
            machine_id=machine_id
        )

    # ========================================================================
    # Callback Handlers (PLC HMI Force Controls)
    # ========================================================================

    async def handle_callback(self, update, context: ContextTypes.DEFAULT_TYPE = None):
        """
        Handle Telegram button callback queries (force controls, emergency stop, refresh).

        Callback Data Format:
            force:<machine_id>:<tag_name>:1    → Force tag ON
            force:<machine_id>:<tag_name>:0    → Force tag OFF
            clear:<machine_id>:<tag_name>      → Clear force
            estop:<machine_id>                 → Emergency stop
            refresh:<machine_id>               → Manual refresh

        Args:
            update: Telegram Update object containing callback_query
            context: Telegram context (optional)

        Example:
            # Register with python-telegram-bot Application
            application.add_handler(CallbackQueryHandler(telegram_adapter.handle_callback))
        """
        # Extract callback_query from Update object
        query = update.callback_query
        callback_data = query.data
        user = query.from_user

        try:
            # Parse callback data
            parts = callback_data.split(":")
            if len(parts) < 2:
                await query.answer("❌ Invalid callback data")
                return

            action = parts[0]
            machine_id = parts[1]

            logger.info(f"Callback from {user.username or user.id}: {callback_data}")

            if action == "force":
                # Force tag to value
                if len(parts) < 4:
                    await query.answer("❌ Invalid force command")
                    return

                tag_name = parts[2]
                value = parts[3] == "1"

                # Verify tag is controllable (not read-only)
                machine = self.machine_config.get_machine(machine_id)
                if machine and tag_name in machine.read_only_tags:
                    await query.answer("❌ Cannot force read-only tag")
                    return

                # Set force
                self.force_provider.set_force(
                    machine_id=machine_id,
                    tag_name=tag_name,
                    value=value,
                    user=f"{user.username or user.id}"
                )

                # Immediately write to Factory.io
                try:
                    await self._write_tag_async(machine_id, tag_name, value)
                except Exception as e:
                    logger.error(f"Failed to write forced value: {e}")
                    await query.answer(f"⚠️ Force set but write failed: {str(e)[:30]}")
                    return

                # Update message
                await self._send_or_edit_message_for_machine(machine_id)

                # Acknowledge
                await query.answer(f"✅ Forced {tag_name} = {'ON' if value else 'OFF'}")

            elif action == "clear":
                # Clear force
                if len(parts) < 3:
                    await query.answer("❌ Invalid clear command")
                    return

                tag_name = parts[2]

                # Release forced tag using Factory.io API
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self.executor,
                    lambda: self.readwrite_tool._run("release", tag_names=[tag_name])
                )

                if "ERROR" in result:
                    logger.error(f"Failed to release {machine_id}.{tag_name}: {result}")
                    await query.answer(f"⚠️ Clear failed: {result[:40]}")
                    return

                # Clear application-level force tracking
                self.force_provider.clear_force(
                    machine_id=machine_id,
                    tag_name=tag_name,
                    user=f"{user.username or user.id}"
                )

                # Update message
                await self._send_or_edit_message_for_machine(machine_id)

                # Acknowledge
                await query.answer(f"✅ Cleared force on {tag_name}")

            elif action == "estop":
                # Emergency stop
                machine = self.machine_config.get_machine(machine_id)
                if not machine:
                    await query.answer("❌ Machine not found")
                    return

                if not machine.emergency_stop_tags:
                    await query.answer("⚠️ No emergency stop tags configured")
                    return

                # Write all emergency stop tags to FALSE
                for tag_name in machine.emergency_stop_tags:
                    try:
                        await self._write_tag_async(machine_id, tag_name, False)
                        logger.warning(f"EMERGENCY STOP: {user.username or user.id} stopped {tag_name}")
                    except Exception as e:
                        logger.error(f"Emergency stop write failed for {tag_name}: {e}")

                # Update message
                await self._send_or_edit_message_for_machine(machine_id)

                # Acknowledge
                await query.answer("⛔ EMERGENCY STOP ACTIVATED")

            elif action == "refresh":
                # Get machine config
                machine = self.machine_config.get_machine(machine_id)
                if not machine:
                    await query.answer("❌ Machine not found")
                    return

                # Get all output tag names
                output_tags = [tag.tag for tag in machine.controllable_outputs]

                # Release ALL forced tags using Factory.io API
                if output_tags:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.executor,
                        lambda: self.readwrite_tool._run("release", tag_names=output_tags)
                    )

                    if "ERROR" in result:
                        logger.error(f"Failed to release forces for {machine_id}: {result}")
                        await query.answer(f"⚠️ Refresh failed: {result[:40]}")
                        return

                # Clear application-level force tracking
                if machine_id in self.force_provider._forced_tags:
                    cleared_count = len(self.force_provider._forced_tags[machine_id])
                    del self.force_provider._forced_tags[machine_id]
                    logger.info(f"Cleared {cleared_count} forced tags for {machine_id}")

                # Manual refresh display
                await self._send_or_edit_message_for_machine(machine_id)
                await query.answer("🔄 Refreshed - All forces cleared")

            else:
                # Unknown action
                logger.warning(f"Unknown callback action: {action}")
                await query.answer(f"❓ Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error handling callback: {e}", exc_info=True)
            try:
                await query.answer(f"❌ Error: {str(e)[:40]}")
            except:
                pass  # Callback may have already timed out
