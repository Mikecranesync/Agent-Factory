#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for WorkOrderService

Tests automatic work order creation from Telegram interactions.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, Mock
from datetime import datetime

from agent_factory.services.work_order_service import WorkOrderService
from agent_factory.services.equipment_matcher import EquipmentMatcher


class MockRivetRequest:
    """Mock RivetRequest for testing."""

    def __init__(self, user_id="telegram_12345", text="Motor not starting", message_type="text"):
        self.user_id = user_id
        self.text = text
        self.message_type = message_type
        self.metadata = {"username": "test_user"}


class MockRivetResponse:
    """Mock RivetResponse for testing."""

    def __init__(
        self,
        text="Check motor contactor",
        confidence=0.85,
        route_taken="B",
        safety_warnings=None,
        suggested_actions=None
    ):
        self.text = text
        self.confidence = confidence
        self.route_taken = Mock(value=route_taken) if isinstance(route_taken, str) else route_taken
        self.safety_warnings = safety_warnings or []
        self.suggested_actions = suggested_actions or ["Check power supply"]
        self.cited_documents = []
        self.links = []
        self.trace = {"trace_id": str(uuid4())}


class TestWorkOrderService:
    """Test suite for WorkOrderService."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        db = Mock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def mock_equipment_matcher(self):
        """Create mock EquipmentMatcher."""
        matcher = Mock(spec=EquipmentMatcher)
        matcher.match_or_create_equipment = AsyncMock()
        matcher.update_equipment_stats = AsyncMock()
        return matcher

    @pytest.fixture
    def work_order_service(self, mock_db, mock_equipment_matcher):
        """Create WorkOrderService instance with mocks."""
        return WorkOrderService(mock_db, mock_equipment_matcher)

    @pytest.mark.asyncio
    async def test_create_work_order_basic(self, work_order_service, mock_db, mock_equipment_matcher):
        """Test basic work order creation."""
        # Setup
        equipment_id = uuid4()
        work_order_id = uuid4()

        mock_equipment_matcher.match_or_create_equipment.return_value = (equipment_id, False)
        mock_db.execute.side_effect = [
            [{"equipment_number": "EQ-2025-0001"}],  # Get equipment number
            [{  # Insert work order
                "id": work_order_id,
                "work_order_number": "WO-2025-0001",
                "created_at": datetime.now()
            }]
        ]

        request = MockRivetRequest()
        response = MockRivetResponse()

        # Execute
        result = await work_order_service.create_from_telegram_interaction(
            request=request,
            response=response
        )

        # Verify
        assert result["id"] == work_order_id
        assert result["work_order_number"] == "WO-2025-0001"
        assert result["equipment_id"] == equipment_id
        mock_equipment_matcher.match_or_create_equipment.assert_called_once()

    @pytest.mark.asyncio
    async def test_priority_calculation_safety_warnings(self, work_order_service):
        """Test priority calculation with safety warnings."""
        # Priority 1: Safety warnings = CRITICAL
        priority = work_order_service._calculate_priority(
            confidence=0.9,
            route="A",
            fault_codes=[],
            safety_warnings=["LOTO required"]
        )
        assert priority == "critical"

    @pytest.mark.asyncio
    async def test_priority_calculation_low_confidence(self, work_order_service):
        """Test priority calculation with low confidence."""
        # Priority 2: Low confidence = HIGH
        priority = work_order_service._calculate_priority(
            confidence=0.3,
            route="C",
            fault_codes=[],
            safety_warnings=[]
        )
        assert priority == "high"

    @pytest.mark.asyncio
    async def test_priority_calculation_critical_fault(self, work_order_service):
        """Test priority calculation with critical fault code."""
        # Priority 3: Critical fault code = HIGH
        priority = work_order_service._calculate_priority(
            confidence=0.8,
            route="A",
            fault_codes=["F7902"],  # F7 prefix = critical
            safety_warnings=[]
        )
        assert priority == "high"

    @pytest.mark.asyncio
    async def test_priority_calculation_normal_fault(self, work_order_service):
        """Test priority calculation with normal fault code."""
        # Normal fault = MEDIUM
        priority = work_order_service._calculate_priority(
            confidence=0.8,
            route="A",
            fault_codes=["F3002"],  # F3 prefix = not critical
            safety_warnings=[]
        )
        assert priority == "medium"

    @pytest.mark.asyncio
    async def test_priority_calculation_default(self, work_order_service):
        """Test default priority calculation."""
        # Default = MEDIUM
        priority = work_order_service._calculate_priority(
            confidence=0.8,
            route="A",
            fault_codes=[],
            safety_warnings=[]
        )
        assert priority == "medium"

    @pytest.mark.asyncio
    async def test_title_generation_with_fault(self, work_order_service):
        """Test title generation with fault code."""
        equipment = {
            "manufacturer": "Siemens",
            "equipment_type": "VFD",
            "fault_codes": ["F3002"]
        }

        title = work_order_service._generate_title("Motor not starting", equipment)

        assert "Siemens" in title
        assert "VFD" in title
        assert "F3002" in title

    @pytest.mark.asyncio
    async def test_title_generation_without_fault(self, work_order_service):
        """Test title generation without fault code."""
        equipment = {
            "manufacturer": "ABB",
            "equipment_type": "PLC",
            "fault_codes": []
        }

        query = "System not responding to commands"
        title = work_order_service._generate_title(query, equipment)

        assert "ABB" in title
        assert "PLC" in title
        assert "System not responding" in title or "commands" in title

    @pytest.mark.asyncio
    async def test_description_building(self, work_order_service):
        """Test work order description building."""
        request = MockRivetRequest(text="VFD showing fault F3002")
        response = MockRivetResponse(text="This fault indicates overcurrent condition. Check motor load.")
        equipment = {
            "manufacturer": "Siemens",
            "model_number": "G120C",
            "serial_number": "SR123456",
            "location": "Building A, Floor 2",
            "fault_codes": ["F3002"]
        }

        description = work_order_service._build_description(request, response, equipment)

        assert "Siemens" in description
        assert "G120C" in description
        assert "SR123456" in description
        assert "Building A" in description
        assert "F3002" in description
        assert "VFD showing fault" in description
        assert "overcurrent" in description

    @pytest.mark.asyncio
    async def test_source_type_mapping(self, work_order_service):
        """Test message type to source type mapping."""
        assert work_order_service._get_source_type("text") == "telegram_text"
        assert work_order_service._get_source_type("voice") == "telegram_voice"
        assert work_order_service._get_source_type("audio") == "telegram_voice"
        assert work_order_service._get_source_type("photo") == "telegram_photo"
        assert work_order_service._get_source_type("image") == "telegram_photo"
        assert work_order_service._get_source_type("unknown") == "telegram_text"  # Default

    @pytest.mark.asyncio
    async def test_symptom_extraction(self, work_order_service):
        """Test symptom keyword extraction."""
        query = "Motor not working, making loud noise and overheating"
        symptoms = work_order_service._extract_symptoms(query)

        assert "not working" in symptoms
        assert "noise" in symptoms
        assert "overheating" in symptoms
        assert len(symptoms) <= 5  # Max 5 symptoms

    @pytest.mark.asyncio
    async def test_update_from_followup(self, work_order_service, mock_db):
        """Test updating work order from follow-up question."""
        # Setup
        work_order_id = uuid4()
        request = MockRivetRequest(text="Follow-up: What about the contactor?")
        response = MockRivetResponse(text="Check contactor coil voltage")

        # Execute
        await work_order_service.update_from_followup(
            work_order_id=work_order_id,
            request=request,
            response=response
        )

        # Verify - should call UPDATE query
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert "UPDATE work_orders" in call_args[0][0]
        # Check that follow-up text is in the arguments (could be in any position)
        all_args_str = str(call_args[0])
        assert "Follow-up" in all_args_str

    @pytest.mark.asyncio
    async def test_update_status(self, work_order_service, mock_db):
        """Test updating work order status."""
        # Setup
        work_order_id = uuid4()

        # Execute
        await work_order_service.update_status(
            work_order_id=work_order_id,
            status="completed",
            notes="Motor contactor replaced"
        )

        # Verify
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert "UPDATE work_orders" in call_args[0][0]
        assert "completed" in call_args[0]

    @pytest.mark.asyncio
    async def test_get_work_order_by_id(self, work_order_service, mock_db):
        """Test fetching work order by ID."""
        # Setup
        work_order_id = uuid4()
        mock_db.execute.return_value = [{
            "id": work_order_id,
            "work_order_number": "WO-2025-0001",
            "title": "Siemens VFD - Fault F3002",
            "status": "open"
        }]

        # Execute
        result = await work_order_service.get_work_order_by_id(work_order_id)

        # Verify
        assert result is not None
        assert result["id"] == work_order_id
        assert result["work_order_number"] == "WO-2025-0001"

    @pytest.mark.asyncio
    async def test_list_work_orders_by_user(self, work_order_service, mock_db):
        """Test listing work orders for a user."""
        # Setup
        user_id = "telegram_12345"
        mock_db.execute.return_value = [
            {"work_order_number": "WO-2025-0001", "title": "VFD Fault"},
            {"work_order_number": "WO-2025-0002", "title": "PLC Issue"}
        ]

        # Execute
        results = await work_order_service.list_work_orders_by_user(user_id, limit=50)

        # Verify
        assert len(results) == 2
        assert results[0]["work_order_number"] == "WO-2025-0001"

    @pytest.mark.asyncio
    async def test_equipment_info_extraction_from_ocr(self, work_order_service):
        """Test equipment info extraction from OCR result."""
        # Setup mock OCR result
        ocr_result = Mock()
        ocr_result.manufacturer = "Siemens"
        ocr_result.model_number = "G120C"
        ocr_result.fault_code = "F3002"

        request = MockRivetRequest()
        response = MockRivetResponse()

        # Execute
        equipment = work_order_service._extract_equipment_info(
            request=request,
            response=response,
            ocr_result=ocr_result,
            machine_id=None
        )

        # Verify
        assert equipment["manufacturer"] == "Siemens"
        assert equipment["model_number"] == "G120C"
        assert "F3002" in equipment["fault_codes"]

    @pytest.mark.asyncio
    async def test_equipment_info_extraction_from_trace(self, work_order_service):
        """Test equipment info extraction from response trace."""
        # Setup
        request = MockRivetRequest()
        response = MockRivetResponse()
        response.trace = {
            "vendor_detection": {"vendor": "Rockwell"},
            "equipment_info": {
                "equipment_type": "PLC",
                "fault_codes": ["E0001"]
            }
        }

        # Execute
        equipment = work_order_service._extract_equipment_info(
            request=request,
            response=response,
            ocr_result=None,
            machine_id=None
        )

        # Verify
        assert equipment["manufacturer"] == "Rockwell"
        assert equipment["equipment_type"] == "PLC"
        assert "E0001" in equipment["fault_codes"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
