"""
Demo version with mock data - For demonstration purposes
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_mock_index_data(index_code: str, days: int = 250) -> pd.DataFrame:
    """Generate mock index data for demonstration"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

    # Generate random walk price data
    np.random.seed(hash(index_code) % 2**32)
    base_price = 3000 if '000001' in index_code else 10000
    returns = np.random.normal(0.001, 0.02, days)
    prices = base_price * (1 + returns).cumprod()

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'high': prices * (1 + np.random.uniform(0, 0.02, days)),
        'low': prices * (1 - np.random.uniform(0, 0.02, days)),
        'close': prices,
        'volume': np.random.randint(100000000, 500000000, days)
    })

    return df

def generate_mock_stock_quote(symbol: str) -> dict:
    """Generate mock stock quote"""
    base_price = np.random.uniform(10, 1000)
    change_pct = np.random.uniform(-5, 5)

    return {
        'code': symbol,
        'name': f'测试股票{symbol}',
        'price': round(base_price, 2),
        'open': round(base_price * (1 + np.random.uniform(-0.02, 0.02)), 2),
        'high': round(base_price * (1 + np.random.uniform(0, 0.03)), 2),
        'low': round(base_price * (1 - np.random.uniform(0, 0.03)), 2),
        'volume': np.random.randint(1000000, 50000000),
        'change_pct': round(change_pct, 2),
        'market_cap': round(base_price * np.random.uniform(1, 10) * 100000000, 2)
    }

# Test
if __name__ == "__main__":
    print("Mock index data:")
    df = generate_mock_index_data('000001', 30)
    print(df.tail())

    print("\nMock stock quote:")
    quote = generate_mock_stock_quote('600519')
    print(quote)
