#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Work Order Service - CMMS Work Order Creation from Telegram Interactions

Creates CMMS work orders automatically from every technician interaction.
Implements equipment-first architecture with automatic equipment matching.

Usage:
    from agent_factory.services.work_order_service import WorkOrderService

    service = WorkOrderService(db, equipment_matcher)
    work_order = await service.create_from_telegram_interaction(
        request=rivet_request,
        response=rivet_response,
        ocr_result=ocr_result,
        machine_id=machine_id,
        conversation_id=conversation_id
    )
"""

import os
import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timedelta

from agent_factory.services.equipment_matcher import EquipmentMatcher

logger = logging.getLogger(__name__)


class WorkOrderService:
    """Service for creating CMMS work orders from Telegram interactions."""

    def __init__(self, db, equipment_matcher: Optional[EquipmentMatcher] = None):
        """
        Initialize work order service.

        Args:
            db: Database connection
            equipment_matcher: EquipmentMatcher instance (created if not provided)
        """
        self.db = db
        self.equipment_matcher = equipment_matcher or EquipmentMatcher(db)

    async def create_from_telegram_interaction(
        self,
        request,  # RivetRequest
        response,  # RivetResponse
        ocr_result = None,  # Optional[OCRResult]
        machine_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Create work order from a Telegram troubleshooting interaction.

        This is called after RIVET orchestrator generates a response.

        Flow:
        1. Extract equipment details (from request, response, OCR, machine library)
        2. Match or create equipment in CMMS (equipment-first architecture)
        3. Generate work order title from question + equipment
        4. Build description with context
        5. Calculate priority from confidence + fault severity + safety warnings
        6. Insert work order linked to equipment
        7. Update equipment statistics

        Args:
            request: RivetRequest with user query
            response: RivetResponse from orchestrator
            ocr_result: Optional OCR result (if photo was analyzed)
            machine_id: Optional link to user's machine library
            conversation_id: Optional conversation ID for multi-turn tracking

        Returns:
            Dictionary with work order details:
            {
                "id": UUID,
                "work_order_number": "WO-2025-0001",
                "equipment_id": UUID,
                "equipment_number": "EQ-2025-0001",
                "created_at": datetime
            }

        Example:
            >>> work_order = await service.create_from_telegram_interaction(
            ...     request=request,
            ...     response=response,
            ...     ocr_result=ocr_result,
            ...     machine_id=machine_id,
            ...     conversation_id=conversation_id
            ... )
            >>> print(f"Work order created: {work_order['work_order_number']}")
        """

        try:
            # 1. Extract equipment details
            equipment = self._extract_equipment_info(request, response, ocr_result, machine_id)

            # 2. MATCH OR CREATE EQUIPMENT IN CMMS (equipment-first architecture)
            equipment_id, is_new_equipment = await self.equipment_matcher.match_or_create_equipment(
                manufacturer=equipment.get("manufacturer"),
                model_number=equipment.get("model_number"),
                serial_number=equipment.get("serial_number"),
                equipment_type=equipment.get("equipment_type"),
                location=equipment.get("location"),
                user_id=request.user_id,
                machine_id=machine_id
            )

            # Get equipment number for denormalization
            eq_result = await self.db.execute("""
                SELECT equipment_number FROM cmms_equipment WHERE id = $1
            """, equipment_id)
            equipment_number = eq_result[0]["equipment_number"] if eq_result else None

            logger.info(
                f"Equipment {'CREATED' if is_new_equipment else 'MATCHED'}: "
                f"{equipment_number} (ID: {equipment_id})"
            )

            # 3. Generate title from question + equipment
            title = self._generate_title(request.text, equipment)

            # 4. Build description with context
            description = self._build_description(request, response, equipment)

            # 5. Calculate priority from confidence + fault severity + safety warnings
            priority = self._calculate_priority(
                confidence=response.confidence,
                route=(response.route_taken.value if hasattr(response.route_taken, 'value') else response.route_taken)[0],  # Extract just the letter (A/B/C/D)
                fault_codes=equipment.get("fault_codes", []),
                safety_warnings=response.safety_warnings or []
            )

            # 6. Determine source type
            source = self._get_source_type(request.message_type)

            # 7. Insert work order (WITH EQUIPMENT LINK)
            work_order_result = await self.db.execute("""
                INSERT INTO work_orders (
                    user_id, telegram_username, created_by_agent, source,
                    manufacturer, model_number, serial_number, equipment_type,
                    machine_id, location,
                    equipment_id, equipment_number,
                    title, description, fault_codes, symptoms,
                    answer_text, confidence_score, route_taken,
                    suggested_actions, safety_warnings, cited_kb_atoms, manual_links,
                    status, priority,
                    trace_id, conversation_id, research_triggered, enrichment_triggered
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7, $8,
                    $9, $10,
                    $11, $12,
                    $13, $14, $15, $16,
                    $17, $18, $19,
                    $20, $21, $22, $23,
                    $24, $25,
                    $26, $27, $28, $29
                )
                RETURNING id, work_order_number, created_at
            """,
                request.user_id,
                request.metadata.get("username") if hasattr(request, 'metadata') and request.metadata else None,
                response.agent_id.value if hasattr(response, 'agent_id') and hasattr(response.agent_id, 'value') else "unknown_agent",
                source,
                equipment.get("manufacturer"),
                equipment.get("model_number"),
                equipment.get("serial_number"),
                equipment.get("equipment_type"),
                str(machine_id) if machine_id else None,
                equipment.get("location"),
                str(equipment_id),  # Equipment ID
                equipment_number,  # Equipment number (denormalized)
                title,
                description,
                equipment.get("fault_codes", []),
                self._extract_symptoms(request.text),
                response.text,
                response.confidence,
                (response.route_taken.value if hasattr(response.route_taken, 'value') else response.route_taken)[0],  # Extract just the letter (A/B/C/D)
                response.suggested_actions or [],
                response.safety_warnings or [],
                [doc.get("id") for doc in (response.cited_documents or [])] if hasattr(response, 'cited_documents') else [],
                response.links or [] if hasattr(response, 'links') else [],
                'open',
                priority,
                str(response.trace.get("trace_id")) if hasattr(response, 'trace') and response.trace and response.trace.get("trace_id") else None,
                str(conversation_id) if conversation_id else None,
                getattr(response, 'research_triggered', False),
                getattr(response, 'kb_enrichment_triggered', False)
            )

            work_order = work_order_result[0]

            logger.info(
                f"Work order created: {work_order['work_order_number']} "
                f"for user {request.user_id} (equipment: {equipment_number})"
            )

            # 8. Update equipment statistics (fault code only - counts updated by trigger)
            fault_code = equipment.get("fault_codes", [None])[0]  # First fault code
            if fault_code:
                await self.equipment_matcher.update_equipment_stats(
                    equipment_id=UUID(equipment_id) if isinstance(equipment_id, str) else equipment_id,
                    fault_code=fault_code
                )

            return {
                "id": work_order["id"],
                "work_order_number": work_order["work_order_number"],
                "equipment_id": equipment_id,
                "equipment_number": equipment_number,
                "created_at": work_order["created_at"]
            }

        except Exception as e:
            logger.error(f"Failed to create work order: {e}", exc_info=True)
            raise

    async def update_from_followup(
        self,
        work_order_id: UUID,
        request,  # RivetRequest
        response  # RivetResponse
    ) -> None:
        """
        Update existing work order when user asks follow-up questions.

        Used when multi-turn conversation continues within 10-minute window.

        Args:
            work_order_id: UUID of existing work order
            request: RivetRequest with follow-up question
            response: RivetResponse from orchestrator
        """
        try:
            # Append to description
            await self.db.execute("""
                UPDATE work_orders
                SET
                    description = description || $1 || $2 || $3 || $4,
                    answer_text = $5,
                    confidence_score = GREATEST(confidence_score, $6),
                    updated_at = NOW()
                WHERE id = $7
            """,
                '\n\n--- Follow-up ---\n',
                request.text,
                '\n\nResponse: ',
                response.text[:200] + "...",  # Truncate for summary
                response.text,  # Full answer replaces previous
                response.confidence,
                str(work_order_id) if isinstance(work_order_id, UUID) else work_order_id
            )

            logger.info(f"Updated work order {work_order_id} with follow-up")

        except Exception as e:
            logger.error(f"Failed to update work order: {e}", exc_info=True)
            raise

    async def update_status(
        self,
        work_order_id: UUID,
        status: str,
        notes: Optional[str] = None
    ) -> None:
        """
        Update work order status (open → in_progress → completed).

        Args:
            work_order_id: UUID of work order
            status: New status ('open', 'in_progress', 'completed', 'cancelled')
            notes: Optional notes to append to description
        """
        try:
            await self.db.execute("""
                UPDATE work_orders
                SET
                    status = $1,
                    description = CASE
                        WHEN $2 IS NOT NULL THEN description || $3 || $2
                        ELSE description
                    END,
                    updated_at = NOW(),
                    completed_at = CASE WHEN $1 = 'completed' THEN NOW() ELSE completed_at END
                WHERE id = $4
            """,
                status,
                notes,
                '\n\n--- Status Update ---\n',
                str(work_order_id) if isinstance(work_order_id, UUID) else work_order_id
            )

            logger.info(f"Updated work order {work_order_id} status to: {status}")

        except Exception as e:
            logger.error(f"Failed to update work order status: {e}", exc_info=True)
            raise

    async def update_feedback(
        self,
        session_id: int,
        feedback_type: str  # 'positive' or 'negative'
    ) -> Optional[List[str]]:
        """
        Update work order feedback and return cited knowledge atom IDs.

        Args:
            session_id: Troubleshooting session ID
            feedback_type: 'positive' or 'negative'

        Returns:
            List of cited knowledge atom IDs (for updating atom success_rate)
        """
        try:
            # Update work_orders table with feedback
            import asyncio

            result = await asyncio.to_thread(
                self.db.execute_query,
                """
                UPDATE work_orders
                SET
                    user_feedback = $1,
                    feedback_at = NOW(),
                    updated_at = NOW()
                WHERE id::text = $2
                RETURNING cited_kb_atoms
                """,
                (feedback_type, str(session_id)),
                fetch_mode="one"
            )

            if result:
                cited_atoms = result[0] if isinstance(result, tuple) else result.get('cited_kb_atoms', [])
                logger.info(f"Updated work order {session_id} feedback to: {feedback_type}, cited atoms: {cited_atoms}")
                return cited_atoms or []
            else:
                logger.warning(f"No work order found with session_id: {session_id}")
                return []

        except Exception as e:
            logger.error(f"Failed to update work order feedback: {e}", exc_info=True)
            return []

    async def create_with_equipment(
        self,
        equipment_id: UUID,
        request,  # RivetRequest
        response  # RivetResponse
    ) -> Dict[str, Any]:
        """
        Create work order with existing equipment ID (used by simulator).

        Simpler version of create_from_telegram_interaction() that skips
        equipment matching and directly uses provided equipment_id.

        Args:
            equipment_id: UUID of existing equipment in cmms_equipment table
            request: RivetRequest with user query
            response: RivetResponse from orchestrator

        Returns:
            Dictionary with work order details

        Example:
            >>> work_order = await service.create_with_equipment(
            ...     equipment_id=equipment_id,
            ...     request=request,
            ...     response=response
            ... )
        """
        try:
            # Get equipment details for denormalization
            equipment_record = await self.equipment_matcher.get_equipment_by_id(equipment_id)
            if not equipment_record:
                raise ValueError(f"Equipment {equipment_id} not found")

            equipment_number = equipment_record["equipment_number"]
            manufacturer = equipment_record.get("manufacturer", "Unknown")
            model_number = equipment_record.get("model_number")
            equipment_type = equipment_record.get("equipment_type")

            # Generate title
            title = f"{manufacturer} {equipment_type or ''} - {request.text[:50]}".strip()
            if len(request.text) > 50:
                title += "..."

            # Build description
            description = f"User query: {request.text}\n\nAI Response: {response.text}"

            # Calculate priority
            priority = "medium"  # Simplified for simulator
            if response.confidence < 0.7:
                priority = "high"
            elif response.confidence > 0.9:
                priority = "low"

            # Determine source type from request
            from agent_factory.rivet_pro.models import MessageType
            source = "telegram_text"
            if request.message_type == MessageType.IMAGE:
                source = "telegram_photo"
            elif request.message_type == MessageType.AUDIO:
                source = "telegram_voice"

            # Insert work order
            work_order_result = await self.db.execute_query_async("""
                INSERT INTO work_orders (
                    equipment_id,
                    equipment_number,
                    manufacturer,
                    model_number,
                    equipment_type,
                    user_id,
                    title,
                    description,
                    answer_text,
                    route_taken,
                    confidence_score,
                    status,
                    priority,
                    source
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                RETURNING id, work_order_number, created_at
            """,
                (str(equipment_id),
                equipment_number,
                manufacturer,
                model_number,
                equipment_type,
                request.user_id,
                title,
                description,
                response.text,
                (response.route_taken.value if hasattr(response.route_taken, 'value') else str(response.route_taken))[0],  # Extract just the letter (A/B/C/D)
                response.confidence,
                'open',
                priority,
                source),
                fetch_mode="one"
            )

            work_order = work_order_result

            logger.info(
                f"Work order created: {work_order['work_order_number']} "
                f"for user {request.user_id} (equipment: {equipment_number})"
            )

            return {
                "id": work_order["id"],
                "work_order_number": work_order["work_order_number"],
                "equipment_id": str(equipment_id),
                "equipment_number": equipment_number,
                "created_at": work_order["created_at"]
            }

        except Exception as e:
            logger.error(f"Failed to create work order with equipment: {e}", exc_info=True)
            raise

    def _extract_equipment_info(
        self,
        request,
        response,
        ocr_result,
        machine_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """
        Merge equipment info from multiple sources.

        Priority order:
        1. Machine library (if selected)
        2. OCR result (if photo)
        3. Intent detector from trace

        Args:
            request: RivetRequest
            response: RivetResponse
            ocr_result: Optional OCR result
            machine_id: Optional machine library ID

        Returns:
            Dictionary with equipment details
        """
        equipment = {}

        # Priority 1: Machine library (if selected)
        # Note: Would need to query user_machines table here
        # Skipping for now - can be added later

        # Priority 2: OCR result (if photo)
        if ocr_result:
            equipment.update({
                "manufacturer": getattr(ocr_result, 'manufacturer', None) or equipment.get("manufacturer"),
                "model_number": getattr(ocr_result, 'model_number', None) or equipment.get("model_number"),
                "fault_codes": [ocr_result.fault_code] if getattr(ocr_result, 'fault_code', None) else []
            })

        # Priority 3: Intent detector from trace
        trace = response.trace or {} if hasattr(response, 'trace') else {}
        if "vendor_detection" in trace:
            equipment.setdefault("manufacturer", trace["vendor_detection"].get("vendor"))

        if "equipment_info" in trace:
            eq_info = trace["equipment_info"]
            equipment.setdefault("equipment_type", eq_info.get("equipment_type"))
            equipment.setdefault("fault_codes", eq_info.get("fault_codes", []))

        return equipment

    def _generate_title(self, query: str, equipment: Dict) -> str:
        """
        Auto-generate work order title.

        Format:
        - With fault code: "Siemens VFD - Fault F3002"
        - Without fault: "Siemens VFD - Motor not starting"

        Args:
            query: User query text
            equipment: Equipment details dictionary

        Returns:
            Generated title string
        """
        manufacturer = equipment.get("manufacturer", "Equipment")
        equipment_type = equipment.get("equipment_type", "")
        fault_codes = equipment.get("fault_codes", [])

        if fault_codes:
            return f"{manufacturer} {equipment_type} - Fault {fault_codes[0]}".strip()
        else:
            # Extract first 50 chars of question
            summary = query[:50].strip()
            if len(query) > 50:
                summary += "..."
            return f"{manufacturer} {equipment_type} - {summary}".strip()

    def _build_description(
        self,
        request,
        response,
        equipment: Dict
    ) -> str:
        """
        Build detailed work order description.

        Includes:
        - Equipment context (manufacturer, model, serial, location, fault codes)
        - User's original question
        - AI-generated response (truncated to 500 chars)

        Args:
            request: RivetRequest
            response: RivetResponse
            equipment: Equipment details dictionary

        Returns:
            Formatted description string
        """
        parts = []

        # Equipment context
        if equipment.get("manufacturer"):
            parts.append(f"**Equipment:** {equipment['manufacturer']} {equipment.get('model_number', '')}".strip())
        if equipment.get("serial_number"):
            parts.append(f"**Serial Number:** {equipment['serial_number']}")
        if equipment.get("location"):
            parts.append(f"**Location:** {equipment['location']}")
        if equipment.get("fault_codes"):
            parts.append(f"**Fault Codes:** {', '.join(equipment['fault_codes'])}")

        parts.append("")  # Blank line

        # User's original question
        parts.append(f"**Issue Description:**\n{request.text}")

        parts.append("")  # Blank line

        # RIVET response (truncated)
        response_text = response.text[:500]
        if len(response.text) > 500:
            response_text += "..."
        parts.append(f"**AI-Generated Response:**\n{response_text}")

        return "\n".join(parts)

    def _calculate_priority(
        self,
        confidence: float,
        route: str,
        fault_codes: List[str],
        safety_warnings: List[str]
    ) -> str:
        """
        Calculate work order priority from response metadata.

        Priority Rules:
        1. Safety warnings = CRITICAL
        2. Low confidence (Route C/D or <0.5) = HIGH
        3. Critical fault codes (F7, F8, F9, E prefix) = HIGH
        4. Other fault codes = MEDIUM
        5. Default = MEDIUM

        Args:
            confidence: AI confidence score (0.0-1.0)
            route: Routing decision (A/B/C/D)
            fault_codes: List of fault codes
            safety_warnings: List of safety warnings

        Returns:
            Priority level ('low', 'medium', 'high', 'critical')
        """
        # Priority 1: Safety warnings = CRITICAL
        if safety_warnings:
            return "critical"

        # Priority 2: Low confidence (Route C/D) = HIGH
        if route in ["C", "D"] or confidence < 0.5:
            return "high"

        # Priority 3: Fault codes = MEDIUM to HIGH
        if fault_codes:
            # Check if critical fault (e.g., F-prefix high numbers)
            critical_faults = ["F7", "F8", "F9", "E"]  # Common critical prefixes
            if any(fc.startswith(prefix) for fc in fault_codes for prefix in critical_faults):
                return "high"
            return "medium"

        # Default: MEDIUM
        return "medium"

    def _get_source_type(self, message_type: str) -> str:
        """
        Map message type to source enum.

        Args:
            message_type: Message type from RivetRequest

        Returns:
            Source type string ('telegram_text', 'telegram_voice', 'telegram_photo')
        """
        mapping = {
            "text": "telegram_text",
            "audio": "telegram_voice",
            "voice": "telegram_voice",
            "photo": "telegram_photo",
            "image": "telegram_photo"
        }
        return mapping.get(message_type, "telegram_text")

    def _extract_symptoms(self, query: str) -> List[str]:
        """
        Extract symptom keywords from user query.

        Simple keyword extraction (could be enhanced with NLP).

        Args:
            query: User query text

        Returns:
            List of detected symptom keywords (max 5)
        """
        # Simple keyword extraction
        symptom_keywords = [
            "not working", "error", "fault", "alarm", "stopped", "overheating",
            "vibration", "noise", "leak", "slow", "stuck", "broken",
            "flashing", "won't start", "won't stop", "intermittent", "tripping"
        ]

        found = []
        query_lower = query.lower()
        for keyword in symptom_keywords:
            if keyword in query_lower:
                found.append(keyword)

        return found[:5]  # Max 5 symptoms

    async def get_work_order_by_id(self, work_order_id: UUID) -> Optional[Dict]:
        """
        Get work order details by ID.

        Args:
            work_order_id: UUID of work order

        Returns:
            Work order record if found, None otherwise
        """
        try:
            result = await self.db.execute("""
                SELECT
                    id,
                    work_order_number,
                    equipment_id,
                    equipment_number,
                    user_id,
                    title,
                    description,
                    status,
                    priority,
                    fault_codes,
                    confidence_score,
                    route_taken,
                    created_at,
                    updated_at,
                    completed_at
                FROM work_orders
                WHERE id = $1
            """, str(work_order_id) if isinstance(work_order_id, UUID) else work_order_id)

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Error fetching work order: {e}")
            return None

    async def list_work_orders_by_user(
        self,
        user_id: str,
        limit: int = 50
    ) -> list[Dict]:
        """
        List work orders for a user.

        Args:
            user_id: User ID to filter by
            limit: Maximum number of results (default 50)

        Returns:
            List of work order records
        """
        try:
            results = await self.db.execute("""
                SELECT
                    id,
                    work_order_number,
                    equipment_number,
                    title,
                    status,
                    priority,
                    created_at
                FROM work_orders
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """, user_id, limit)

            return results or []

        except Exception as e:
            logger.error(f"Error listing work orders: {e}")
            return []
