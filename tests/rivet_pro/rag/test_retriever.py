"""
Tests for RIVET Pro RAG Retriever

Phase 2/8 - RAG Layer Tests
"""

import pytest
from unittest.mock import Mock
from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType, KBCoverage
from agent_factory.rivet_pro.rag import search_docs, estimate_coverage
from agent_factory.rivet_pro.rag.config import RetrievedDoc, RAGConfig


class TestSearchDocs:
    def test_search_with_siemens_intent(self, monkeypatch):
        mock_client = Mock()
        monkeypatch.setattr(
            "agent_factory.rivet_pro.rag.retriever.get_supabase_client",
            lambda: mock_client
        )
        mock_client.from_ = Mock(return_value=Mock())
        mock_client.from_().select = Mock(return_value=Mock())
        mock_client.from_().select().limit = Mock(return_value=Mock())
        mock_client.from_().select().limit().execute = Mock(return_value=Mock(data=[]))
        
        intent = RivetIntent(
            vendor=VendorType.SIEMENS,
            equipment_type=EquipmentType.VFD,
            raw_summary="G120C fault F3002",
            detected_fault_codes=["F3002"],
            confidence=0.9,
            kb_coverage="strong"
        )
        
        docs = search_docs(intent, agent_id="siemens", top_k=8)
        assert isinstance(docs, list)

    def test_search_with_no_client(self, monkeypatch):
        monkeypatch.setattr(
            "agent_factory.rivet_pro.rag.retriever.get_supabase_client",
            lambda: None
        )
        intent = RivetIntent(
            vendor=VendorType.SIEMENS,
            equipment_type=EquipmentType.VFD,
            raw_summary="test",
            confidence=0.9,
            kb_coverage="strong"
        )
        docs = search_docs(intent)
        assert docs == []


class TestEstimateCoverage:
    def test_strong_coverage(self, monkeypatch):
        def mock_search(intent, agent_id, top_k):
            return [Mock(spec=RetrievedDoc) for _ in range(10)]
        monkeypatch.setattr(
            "agent_factory.rivet_pro.rag.retriever.search_docs",
            mock_search
        )
        intent = RivetIntent(
            vendor=VendorType.SIEMENS,
            equipment_type=EquipmentType.VFD,
            raw_summary="test",
            confidence=0.9,
            kb_coverage="strong"
        )
        coverage = estimate_coverage(intent)
        assert coverage == KBCoverage.STRONG

    def test_none_coverage(self, monkeypatch):
        def mock_search(intent, agent_id, top_k):
            return []
        monkeypatch.setattr(
            "agent_factory.rivet_pro.rag.retriever.search_docs",
            mock_search
        )
        intent = RivetIntent(
            vendor=VendorType.UNKNOWN,
            equipment_type=EquipmentType.UNKNOWN,
            raw_summary="test",
            confidence=0.4,
            kb_coverage="none"
        )
        coverage = estimate_coverage(intent)
        assert coverage == KBCoverage.NONE


class TestRetrievedDocModel:
    def test_retrieved_doc_creation(self):
        doc = RetrievedDoc(
            atom_id="siemens:g120c:f3002",
            title="G120C Fault F3002",
            summary="DC bus overvoltage fault",
            content="F3002 indicates overvoltage",
            atom_type="fault",
            vendor="siemens",
            equipment_type="vfd"
        )
        assert doc.atom_id == "siemens:g120c:f3002"
        assert doc.vendor == "siemens"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
