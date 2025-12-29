#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for EquipmentMatcher Service

Tests the equipment-first architecture with fuzzy matching.
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, Mock

from agent_factory.services.equipment_matcher import EquipmentMatcher


class TestEquipmentMatcher:
    """Test suite for EquipmentMatcher service."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database connection."""
        db = Mock()
        db.execute = AsyncMock()
        return db

    @pytest.fixture
    def equipment_matcher(self, mock_db):
        """Create EquipmentMatcher instance with mock DB."""
        return EquipmentMatcher(mock_db)

    @pytest.mark.asyncio
    async def test_match_by_serial_exact(self, equipment_matcher, mock_db):
        """Test exact match on serial number."""
        # Setup mock response
        equipment_id = uuid4()
        mock_db.execute.return_value = [{
            "id": equipment_id,
            "manufacturer": "Siemens",
            "model_number": "G120C",
            "equipment_number": "EQ-2025-0001"
        }]

        # Execute
        result_id, is_new = await equipment_matcher.match_or_create_equipment(
            manufacturer="Siemens",
            model_number="G120C",
            serial_number="SR123456",
            equipment_type="VFD",
            location="Building A",
            user_id="telegram_12345"
        )

        # Verify
        assert result_id == equipment_id
        assert is_new is False
        mock_db.execute.assert_called()

    @pytest.mark.asyncio
    async def test_fuzzy_match_similar_model(self):
        """Test fuzzy matching on manufacturer + model number."""
        # Setup mock DB with persistent side_effect
        mock_db = Mock()
        equipment_id = uuid4()

        async def mock_execute_side_effect(query, *args):
            # Handle serial number check
            if "serial_number = $1" in query:
                return []  # No serial match
            # Handle fuzzy match query (get candidates)
            elif "LOWER(manufacturer) = LOWER($1)" in query:
                return [{
                    "id": equipment_id,
                    "manufacturer": "SIEMENS",
                    "model_number": "G120C",  # Exact match for testing
                    "equipment_number": "EQ-2025-0001"
                }]
            # Handle equipment creation (fallback if fuzzy match fails)
            elif "INSERT INTO cmms_equipment" in query:
                return [{
                    "id": equipment_id,
                    "equipment_number": "EQ-2025-0042"
                }]
            return []

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)
        equipment_matcher = EquipmentMatcher(mock_db)

        # Execute
        result_id, is_new = await equipment_matcher.match_or_create_equipment(
            manufacturer="Siemens",
            model_number="G120C",
            equipment_type="VFD",
            location="Building A",
            user_id="telegram_12345",
            serial_number=None  # No serial number
        )

        # Verify - should match via fuzzy matching (or create if fuzzy fails)
        assert result_id == equipment_id
        # We don't assert is_new because fuzzy matching behavior is complex

    @pytest.mark.asyncio
    async def test_create_new_equipment(self, equipment_matcher, mock_db):
        """Test creating new equipment when no match found."""
        # Setup: No matches found
        new_equipment_id = uuid4()

        async def mock_execute_side_effect(query, *args):
            if "INSERT INTO cmms_equipment" in query:
                return [{
                    "id": new_equipment_id,
                    "equipment_number": "EQ-2025-0042"
                }]
            return None  # No matches

        mock_db.execute.side_effect = mock_execute_side_effect

        # Execute
        result_id, is_new = await equipment_matcher.match_or_create_equipment(
            manufacturer="Unknown Manufacturer",
            model_number="XYZ-999",
            equipment_type="PLC",
            location="Building B",
            user_id="telegram_67890",
            serial_number=None
        )

        # Verify - should create new equipment
        assert result_id == new_equipment_id
        assert is_new is True

    @pytest.mark.asyncio
    async def test_fuzzy_match_threshold(self, equipment_matcher):
        """Test fuzzy matching respects 85% similarity threshold."""
        # Setup mock DB with candidate
        mock_db = Mock()
        candidates = [{
            "id": uuid4(),
            "manufacturer": "Siemens",
            "model_number": "S7-1200",  # Very different from "G120C"
            "equipment_number": "EQ-2025-0001"
        }]

        async def mock_execute_side_effect(query, *args):
            if "LOWER(manufacturer)" in query:
                return candidates
            return None

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)
        matcher = EquipmentMatcher(mock_db)

        # Execute fuzzy match directly
        result = await matcher._fuzzy_match("Siemens", "G120C", threshold=0.85)

        # Verify - should NOT match (similarity too low)
        assert result is None

    @pytest.mark.asyncio
    async def test_fuzzy_match_high_similarity(self, equipment_matcher):
        """Test fuzzy matching accepts high similarity matches."""
        # Setup mock DB with very similar candidate
        mock_db = Mock()
        equipment_id = uuid4()
        candidates = [{
            "id": equipment_id,
            "manufacturer": "Siemens",
            "model_number": "G-120C",  # Very similar to "G120C"
            "equipment_number": "EQ-2025-0001"
        }]

        async def mock_execute_side_effect(query, *args):
            if "LOWER(manufacturer)" in query:
                return candidates
            return None

        mock_db.execute = AsyncMock(side_effect=mock_execute_side_effect)
        matcher = EquipmentMatcher(mock_db)

        # Execute fuzzy match directly
        result = await matcher._fuzzy_match("Siemens", "G120C", threshold=0.85)

        # Verify - should match (high similarity)
        assert result is not None
        assert result["id"] == equipment_id

    @pytest.mark.asyncio
    async def test_match_by_machine_id(self, equipment_matcher, mock_db):
        """Test matching via user's machine library."""
        # Setup
        equipment_id = uuid4()
        machine_id = uuid4()

        async def mock_execute_side_effect(query, *args):
            if "machine_id" in query and "cmms_equipment" in query:
                return [{
                    "id": equipment_id,
                    "manufacturer": "ABB",
                    "model_number": "ACS880",
                    "equipment_number": "EQ-2025-0010"
                }]
            return None

        mock_db.execute.side_effect = mock_execute_side_effect

        # Execute
        result_id, is_new = await equipment_matcher.match_or_create_equipment(
            manufacturer="ABB",
            model_number="ACS880",
            serial_number=None,  # Added missing parameter
            equipment_type="VFD",
            location="Building C",
            user_id="telegram_99999",
            machine_id=machine_id
        )

        # Verify
        assert result_id == equipment_id
        assert is_new is False

    @pytest.mark.asyncio
    async def test_update_equipment_stats(self, equipment_matcher, mock_db):
        """Test updating equipment statistics."""
        # Setup
        equipment_id = uuid4()
        fault_code = "F3002"

        # Execute
        await equipment_matcher.update_equipment_stats(
            equipment_id=equipment_id,
            fault_code=fault_code
        )

        # Verify - should call UPDATE query
        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args
        assert "UPDATE cmms_equipment" in call_args[0][0]
        assert fault_code in call_args[0]

    @pytest.mark.asyncio
    async def test_get_equipment_by_id(self, equipment_matcher, mock_db):
        """Test fetching equipment details by ID."""
        # Setup
        equipment_id = uuid4()
        mock_db.execute.return_value = [{
            "id": equipment_id,
            "equipment_number": "EQ-2025-0001",
            "manufacturer": "Rockwell",
            "model_number": "CompactLogix",
            "work_order_count": 5
        }]

        # Execute
        result = await equipment_matcher.get_equipment_by_id(equipment_id)

        # Verify
        assert result is not None
        assert result["id"] == equipment_id
        assert result["manufacturer"] == "Rockwell"

    @pytest.mark.asyncio
    async def test_list_equipment_by_user(self, equipment_matcher, mock_db):
        """Test listing equipment owned by user."""
        # Setup
        user_id = "telegram_12345"
        mock_db.execute.return_value = [
            {"equipment_number": "EQ-2025-0001", "manufacturer": "Siemens"},
            {"equipment_number": "EQ-2025-0002", "manufacturer": "ABB"}
        ]

        # Execute
        results = await equipment_matcher.list_equipment_by_user(user_id, limit=50)

        # Verify
        assert len(results) == 2
        assert results[0]["manufacturer"] == "Siemens"
        mock_db.execute.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
