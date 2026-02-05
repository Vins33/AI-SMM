# src/core/schemas.py
"""Pydantic schemas for agent tools."""

from pydantic import BaseModel, Field

# --- Web & Knowledge Base Schemas ---


class WebSearchSchema(BaseModel):
    """Schema for web search tool."""

    query: str = Field(description="The search query to send to Google.")


class KBReadSchema(BaseModel):
    """Schema for KB read tool."""

    query: str = Field(description="The query to search in the knowledge base.")


class KBWriteSchema(BaseModel):
    """Schema for KB write tool."""

    content: str = Field(description="The content to save to the knowledge base.")


# --- Stock Analysis Schemas ---


class StockAnalysisSchema(BaseModel):
    """Schema for stock scoring tool."""

    ticker: str = Field(description="Stock ticker (e.g., AAPL, MSFT, NVDA).")


class StockPriceSchema(BaseModel):
    """Schema for stock price tool."""

    ticker: str = Field(description="Stock ticker (e.g., AAPL, MSFT, NVDA).")
    period: str = Field(
        default="1mo",
        description="Period for historical data: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max",
    )


class CompareStocksSchema(BaseModel):
    """Schema for compare stocks tool."""

    tickers: list[str] = Field(
        description="List of 2-5 stock tickers to compare (e.g., ['AAPL', 'MSFT', 'GOOGL'])."
    )


class DividendAnalysisSchema(BaseModel):
    """Schema for dividend analysis tool."""

    ticker: str = Field(description="Stock ticker (e.g., AAPL, JNJ, KO).")


class CompanyProfileSchema(BaseModel):
    """Schema for company profile tool."""

    ticker: str = Field(description="Stock ticker (e.g., AAPL, MSFT, NVDA).")


class StockNewsSchema(BaseModel):
    """Schema for stock news tool."""

    ticker: str = Field(description="Stock ticker (e.g., AAPL, TSLA, NVDA).")


class TechnicalIndicatorsSchema(BaseModel):
    """Schema for technical indicators tool."""

    ticker: str = Field(description="Stock ticker (e.g., AAPL, MSFT, NVDA).")
    period: str = Field(
        default="3mo",
        description="Period for calculation: 1mo, 3mo, 6mo, 1y",
    )


class EarningsCalendarSchema(BaseModel):
    """Schema for earnings calendar tool."""

    ticker: str = Field(description="Stock ticker (e.g., AAPL, MSFT, NVDA).")
