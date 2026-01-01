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
    edit_threshold_seconds: int = 5

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
        Convert PlatformMessage to Telegram Markdown V2 format.

        Args:
            message: PlatformMessage to convert
            machine_id: ID of machine (for health status)

        Returns:
            Markdown-formatted message text
        """
        # Get health status
        health_info = self.state_manager.get_health_status().get(machine_id, {})
        circuit_state = health_info.get("circuit_state", "closed")

        # Determine status emoji
        if circuit_state == "closed":
            status_emoji = "🟢"
            status_text = ""
        elif circuit_state == "half_open":
            status_emoji = "🟡"
            status_text = " (TESTING)"
        else:  # open
            status_emoji = "🔴"
            status_text = " (OFFLINE)"

        # Build message parts
        parts = []

        # Header with status
        title = ResponseFormatter.escape_markdown(message.title.upper())
        parts.append(f"{status_emoji} *{title}*{status_text}")

        if message.description:
            desc = ResponseFormatter.escape_markdown(message.description)
            parts.append(desc)

        parts.append("")  # Blank line

        # I/O Status - Inputs
        inputs = message.get_inputs()
        if inputs:
            parts.append("📊 *INPUTS:*")
            for tag_name, tag in inputs.items():
                value_str = str(tag.value).upper() if isinstance(tag.value, bool) else str(tag.value)
                value_str = ResponseFormatter.escape_markdown(value_str)
                tag_name_escaped = ResponseFormatter.escape_markdown(tag_name)
                parts.append(f"  • {tag_name_escaped}: {value_str}")
            parts.append("")

        # I/O Status - Outputs
        outputs = message.get_outputs()
        if outputs:
            parts.append("⚙️ *OUTPUTS:*")
            for tag_name, tag in outputs.items():
                value_str = "ON" if tag.value is True else "OFF" if tag.value is False else str(tag.value)
                value_str = ResponseFormatter.escape_markdown(value_str)
                tag_name_escaped = ResponseFormatter.escape_markdown(tag_name)
                parts.append(f"  • {tag_name_escaped}: {value_str}")
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
        Convert PlatformMessage controls to Telegram inline keyboard.

        Args:
            message: PlatformMessage with controls
            machine_id: ID of machine (for callback data)

        Returns:
            InlineKeyboardMarkup with control buttons
        """
        if not message.controls:
            return InlineKeyboardMarkup([])

        # Separate emergency stop from regular controls
        regular_controls = [c for c in message.controls if c.action != "emergency_stop"]
        emergency_controls = [c for c in message.controls if c.action == "emergency_stop"]

        keyboard = []

        # Add regular controls in 2-column layout
        for i in range(0, len(regular_controls), 2):
            row = []
            for j in range(2):
                if i + j < len(regular_controls):
                    control = regular_controls[i + j]
                    button_text = f"{control.emoji} {control.label}" if control.emoji else control.label
                    callback_data = f"factoryio:{control.to_callback_data(machine_id)}"
                    row.append(InlineKeyboardButton(button_text, callback_data=callback_data))
            keyboard.append(row)

        # Add emergency stop button (full width)
        for control in emergency_controls:
            button_text = f"{control.emoji} {control.label}" if control.emoji else control.label
            callback_data = f"factoryio:{control.to_callback_data(machine_id)}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

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

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle Telegram callback query (button click).

        Parses callback_data, validates, executes write, and sends confirmation.

        Args:
            update: Telegram Update object
            context: Telegram context
        """
        query = update.callback_query
        if not query:
            return

        await query.answer()  # Acknowledge button click

        # Parse callback data
        parsed = self._validate_callback_data(query.data)
        if not parsed:
            await query.message.reply_text("❌ Invalid button action")
            return

        action = parsed["action"]
        machine_id = parsed["machine_id"]
        tag_name = parsed["tag_name"]
        value = parsed["value"]

        # Get machine
        machine = self.machine_config.get_machine(machine_id)
        chat_id = query.message.chat_id

        # Check rate limiting
        if not self._check_rate_limit(chat_id):
            await query.answer("⏳ Please wait before pressing another button", show_alert=True)
            return

        # Get username for logging
        username = query.from_user.username or query.from_user.first_name or "Unknown"

        try:
            if action == "toggle":
                # Read current value
                current_state = self.state_manager.get_state(machine_id)
                current_tag = current_state.get(tag_name)

                if current_tag is None:
                    await query.message.reply_text(f"❌ Tag {tag_name} not found in state")
                    return

                # Toggle boolean value
                new_value = not current_tag.value if isinstance(current_tag.value, bool) else False

                # Execute write
                success, message = await self._execute_write(machine_id, tag_name, new_value)

                # Update rate limit
                if success:
                    self._update_write_time(chat_id)

                # Send confirmation
                confirmation = f"@{username} toggled {tag_name}\n{message}"
                await query.message.reply_text(confirmation)

            elif action == "write":
                # Convert value string to appropriate type
                if value.lower() == "true":
                    write_value = True
                elif value.lower() == "false":
                    write_value = False
                elif value.isdigit():
                    write_value = int(value)
                else:
                    try:
                        write_value = float(value)
                    except ValueError:
                        write_value = value  # Keep as string

                # Execute write
                success, message = await self._execute_write(machine_id, tag_name, write_value)

                # Update rate limit
                if success:
                    self._update_write_time(chat_id)

                # Send confirmation
                confirmation = f"@{username} set {tag_name}\n{message}"
                await query.message.reply_text(confirmation)

            elif action == "emergency_stop":
                # Emergency stop - set all emergency_stop_tags to False
                if not machine.emergency_stop_tags:
                    await query.message.reply_text("❌ No emergency stop tags configured")
                    return

                # Execute writes for all emergency stop tags
                results = []
                for stop_tag in machine.emergency_stop_tags:
                    success, message = await self._execute_write(machine_id, stop_tag, False)
                    results.append((stop_tag, success, message))

                # Update rate limit
                self._update_write_time(chat_id)

                # Build confirmation message
                success_count = sum(1 for _, success, _ in results if success)
                confirmation_parts = [
                    f"⚠️ *EMERGENCY STOP* activated by @{username}",
                    f"",
                    f"Results: {success_count}/{len(results)} tags stopped"
                ]

                for tag, success, message in results:
                    status = "✅" if success else "❌"
                    confirmation_parts.append(f"{status} {tag}")

                confirmation = "\n".join(confirmation_parts)
                await query.message.reply_text(
                    ResponseFormatter.escape_markdown(confirmation),
                    parse_mode=ParseMode.MARKDOWN_V2
                )

        except Exception as e:
            logger.error(f"Error handling callback: {e}", exc_info=True)
            await query.message.reply_text(f"❌ Error: {str(e)}")

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
