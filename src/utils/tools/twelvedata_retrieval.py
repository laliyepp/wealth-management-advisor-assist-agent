"""Financial data tool using Twelve Data API."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import httpx

from ..async_utils import rate_limited




class AsyncFinancialDataTool:
    """Financial data tool using Twelve Data API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        max_concurrency: int = 3,
        timeout: float = 30.0,
    ) -> None:
        """Initialize the financial data tool.
        
        Parameters
        ----------
        api_key : str, optional
            API key for Twelve Data service. If not provided, uses TWELVEDATA_API_KEY env var.
        base_url : str, optional
            Base URL for Twelve Data API. If not provided, uses TWELVEDATA_BASE_URL env var.
        max_concurrency : int, optional
            Maximum number of concurrent requests, by default 3
        timeout : float, optional
            Request timeout in seconds, by default 30.0
        """
        self.api_key = api_key or os.getenv("TWELVEDATA_API_KEY")
        self.base_url = (base_url or os.getenv("TWELVEDATA_BASE_URL", "https://api.twelvedata.com")).rstrip("/")
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        self.semaphore = asyncio.Semaphore(max_concurrency)
        
        if not self.api_key:
            raise ValueError("API key is required. Set TWELVEDATA_API_KEY environment variable or pass api_key parameter.")
        
        self._client = httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "User-Agent": "Wealth-Management-Agent/1.0"
            },
            timeout=self.timeout
        )

    async def get_price(self, symbol: str) -> str | None:
        """Get current price for a symbol using Twelve Data /price endpoint.

        Parameters
        ----------
        symbol : str
            The financial symbol to get price for (e.g., "AAPL", "US2Y").

        Returns
        -------
        str | None
            Price as string, or None if error or not found.
        """
        if not symbol.strip():
            return None

        api_url = f"{self.base_url}/price"
        params = {
            "symbol": symbol.upper(),
            "apikey": self.api_key
        }

        try:
            response = await rate_limited(
                lambda: self._client.get(api_url, params=params),
                semaphore=self.semaphore
            )
            response.raise_for_status()
            data = response.json()
            
            self.logger.info(f"Price query: {symbol}; Price: {data.get('price')}")
            return data.get('price')
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error during price request: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"Error during price request: {str(e)}")
            return None

    async def get_time_series(self, symbol: str, interval: str = "1day") -> list[dict[str, str]] | None:
        """Get time series data for a symbol using Twelve Data /time_series endpoint.

        Parameters
        ----------
        symbol : str
            The financial symbol to query (e.g., "US2Y", "AAPL").
        interval : str, optional
            Time interval: 1min, 5min, 15min, 30min, 45min, 1h, 2h, 4h, 5h, 1day, 1week, 1month.
            Default is "1day".

        Returns
        -------
        list[dict[str, str]] | None
            Array of time series data points with datetime, open, high, low, close (volume removed).
            Returns None if error or not found.
        """
        if not symbol.strip():
            return None
            
        # Validate interval
        valid_intervals = ["1min", "5min", "15min", "30min", "45min", "1h", "2h", "4h", "5h", "1day", "1week", "1month"]
        if interval not in valid_intervals:
            self.logger.error(f"Invalid interval: {interval}. Valid intervals: {valid_intervals}")
            return None

        api_url = f"{self.base_url}/time_series"
        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "apikey": self.api_key
        }

        try:
            response = await rate_limited(
                lambda: self._client.get(api_url, params=params),
                semaphore=self.semaphore
            )
            response.raise_for_status()
            data = response.json()
            
            values = data.get('values', [])
            # Remove volume field since it's always 0
            cleaned_values = []
            for item in values:
                cleaned_item = {k: v for k, v in item.items() if k != 'volume'}
                cleaned_values.append(cleaned_item)
            
            self.logger.info(f"Time series query: {symbol} ({interval}); Count: {len(cleaned_values)}")
            return cleaned_values
            
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error during time series request: {e.response.status_code} - {e.response.text}")
            return None
        except Exception as e:
            self.logger.error(f"Error during time series request: {str(e)}")
            return None


    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        _ = exc_type, exc_val, exc_tb  # Unused parameters
        await self.close()


def create_financial_data_tool(
    api_key: str | None = None,
    base_url: str | None = None,
    max_concurrency: int = 3
) -> AsyncFinancialDataTool:
    """Create a financial data tool instance.
    
    Parameters
    ----------
    api_key : str, optional
        API key for Twelve Data service
    base_url : str, optional  
        Base URL for Twelve Data API
    max_concurrency : int, optional
        Maximum number of concurrent requests, by default 3
        
    Returns
    -------
    AsyncFinancialDataTool
        Configured financial data tool instance
    """
    return AsyncFinancialDataTool(
        api_key=api_key,
        base_url=base_url,
        max_concurrency=max_concurrency
    )