# tests/test_schemas.py
"""
Tests for Pydantic schemas.
"""

import pytest
from pydantic import ValidationError

from src.core.schemas import (
    CompanyProfileInput,
    CompareStocksInput,
    DividendAnalysisInput,
    EarningsCalendarInput,
    KnowledgeBaseWriteInput,
    StockNewsInput,
    StockPriceInput,
    StockScoringInput,
    TechnicalIndicatorsInput,
    WebSearchInput,
)


@pytest.mark.unit
class TestWebSearchInput:
    """Tests for WebSearchInput schema."""

    def test_valid_input(self) -> None:
        """Test valid web search input."""
        input_data = WebSearchInput(query="test query")
        assert input_data.query == "test query"

    def test_empty_query_invalid(self) -> None:
        """Test that empty query raises validation error."""
        with pytest.raises(ValidationError):
            WebSearchInput(query="")


@pytest.mark.unit
class TestStockPriceInput:
    """Tests for StockPriceInput schema."""

    def test_valid_symbol(self) -> None:
        """Test valid stock symbol input."""
        input_data = StockPriceInput(symbol="AAPL")
        assert input_data.symbol == "AAPL"

    def test_default_period(self) -> None:
        """Test default period value."""
        input_data = StockPriceInput(symbol="AAPL")
        assert input_data.period == "1mo"

    def test_custom_period(self) -> None:
        """Test custom period value."""
        input_data = StockPriceInput(symbol="AAPL", period="3mo")
        assert input_data.period == "3mo"


@pytest.mark.unit
class TestCompareStocksInput:
    """Tests for CompareStocksInput schema."""

    def test_valid_symbols(self) -> None:
        """Test valid symbols list."""
        input_data = CompareStocksInput(symbols=["AAPL", "GOOGL", "MSFT"])
        assert len(input_data.symbols) == 3
        assert "AAPL" in input_data.symbols

    def test_single_symbol(self) -> None:
        """Test single symbol in list."""
        input_data = CompareStocksInput(symbols=["AAPL"])
        assert len(input_data.symbols) == 1


@pytest.mark.unit
class TestDividendAnalysisInput:
    """Tests for DividendAnalysisInput schema."""

    def test_valid_input(self) -> None:
        """Test valid dividend analysis input."""
        input_data = DividendAnalysisInput(symbol="AAPL")
        assert input_data.symbol == "AAPL"


@pytest.mark.unit
class TestCompanyProfileInput:
    """Tests for CompanyProfileInput schema."""

    def test_valid_input(self) -> None:
        """Test valid company profile input."""
        input_data = CompanyProfileInput(symbol="AAPL")
        assert input_data.symbol == "AAPL"


@pytest.mark.unit
class TestStockNewsInput:
    """Tests for StockNewsInput schema."""

    def test_valid_input(self) -> None:
        """Test valid stock news input."""
        input_data = StockNewsInput(symbol="AAPL")
        assert input_data.symbol == "AAPL"

    def test_default_count(self) -> None:
        """Test default news count."""
        input_data = StockNewsInput(symbol="AAPL")
        assert input_data.count == 5

    def test_custom_count(self) -> None:
        """Test custom news count."""
        input_data = StockNewsInput(symbol="AAPL", count=10)
        assert input_data.count == 10


@pytest.mark.unit
class TestTechnicalIndicatorsInput:
    """Tests for TechnicalIndicatorsInput schema."""

    def test_valid_input(self) -> None:
        """Test valid technical indicators input."""
        input_data = TechnicalIndicatorsInput(symbol="AAPL")
        assert input_data.symbol == "AAPL"


@pytest.mark.unit
class TestEarningsCalendarInput:
    """Tests for EarningsCalendarInput schema."""

    def test_valid_input(self) -> None:
        """Test valid earnings calendar input."""
        input_data = EarningsCalendarInput(symbol="AAPL")
        assert input_data.symbol == "AAPL"


@pytest.mark.unit
class TestStockScoringInput:
    """Tests for StockScoringInput schema."""

    def test_valid_input(self) -> None:
        """Test valid stock scoring input."""
        input_data = StockScoringInput(symbol="AAPL")
        assert input_data.symbol == "AAPL"


@pytest.mark.unit
class TestKnowledgeBaseWriteInput:
    """Tests for KnowledgeBaseWriteInput schema."""

    def test_valid_input(self) -> None:
        """Test valid knowledge base write input."""
        input_data = KnowledgeBaseWriteInput(
            topic="Test Topic",
            content="Test content for knowledge base"
        )
        assert input_data.topic == "Test Topic"
        assert input_data.content == "Test content for knowledge base"

    def test_empty_topic_invalid(self) -> None:
        """Test that empty topic raises validation error."""
        with pytest.raises(ValidationError):
            KnowledgeBaseWriteInput(topic="", content="Some content")

    def test_empty_content_invalid(self) -> None:
        """Test that empty content raises validation error."""
        with pytest.raises(ValidationError):
            KnowledgeBaseWriteInput(topic="Some topic", content="")
