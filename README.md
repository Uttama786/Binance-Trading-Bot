# Binance Trading Bot

A comprehensive CLI-based trading bot for Binance that supports both **Futures** and **Spot** trading with robust logging, validation, and multiple order types.

## 🎯 Current Status

✅ **Spot Trading**: Fully functional and tested  
⚠️ **Futures Trading**: Available but requires futures-enabled API keys  

## ✨ Features

### 🚀 Spot Trading (Ready to Use)
- **Market Orders**: Immediate execution at current market price
- **Limit Orders**: Execution at specified price or better
- **USDT Amount Support**: Place orders using USDT amounts instead of quantities
- **Real-time Execution**: Tested and working with Binance testnet

### 🔄 Futures Trading (Advanced)
- **Market Orders**: Immediate execution for futures contracts
- **Limit Orders**: Futures limit orders with leverage support
- **Stop-Limit Orders**: Trigger limit orders when stop price is hit
- **OCO (One-Cancels-the-Other)**: Place take-profit and stop-loss simultaneously
- **TWAP (Time-Weighted Average Price)**: Split large orders into smaller chunks over time
- **Grid Orders**: Automated buy-low/sell-high within a price range

### 🛡️ Core Features
- **Input Validation**: Comprehensive validation of all trading parameters
- **Structured Logging**: JSON-formatted logs for all actions and errors
- **Configuration Management**: Load settings from config.json or environment variables
- **Error Handling**: Robust error handling with detailed logging
- **Testnet Support**: Safe testing with fake money

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd python

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create or update your `config.json`:

```json
{
    "api_key": "your_binance_api_key",
    "api_secret": "your_binance_api_secret",
    "use_testnet": true,
    "base_url": "https://testnet.binance.vision",
    "log_file": "bot.log",
    "log_level": "INFO",
    "default_leverage": 1,
    "max_position_size": 1000.0,
    "request_timeout": 30,
    "max_retries": 3
}
```

### 3. Get API Keys

**For Spot Trading (Recommended for beginners):**
- Visit: https://testnet.binance.vision/key/generate
- Generate API keys with spot trading permissions
- Add your IP address to whitelist if required

**For Futures Trading:**
- Visit: https://testnet.binancefuture.com
- Generate API keys with futures trading permissions
- Update `base_url` to `"https://testnet.binancefuture.com"`

## 📖 Usage

### 💰 Spot Trading (Current Working Implementation)

#### Market Orders
```bash
# Buy $10 worth of Bitcoin
python -m src.spot_orders BTCUSDT BUY 10 --usdt

# Buy exact quantity of Bitcoin
python -m src.spot_orders BTCUSDT BUY 0.001

# Sell Ethereum
python -m src.spot_orders ETHUSDT SELL 0.01
```

#### Limit Orders
```bash
# Buy Bitcoin when price drops to $50,000
python -m src.spot_limit_orders BTCUSDT BUY 0.001 50000

# Sell Ethereum when price reaches $4,000
python -m src.spot_limit_orders ETHUSDT SELL 0.01 4000
```

### ⚡ Futures Trading (Requires Futures API Keys)

#### Market Orders
```bash
# Basic futures market order
python -m src.market_orders BTCUSDT BUY 0.01

# Market order with USDT amount
python -m src.market_orders BTCUSDT BUY 0.01 --usdt 500

# Reduce-only market order
python -m src.market_orders BTCUSDT SELL 0.01 --reduce-only
```

#### Limit Orders
```bash
# Basic futures limit order
python -m src.limit_orders BTCUSDT BUY 0.01 50000

# Limit order with custom time-in-force
python -m src.limit_orders BTCUSDT SELL 0.1 55000 --time-in-force IOC

# Limit order with USDT amount
python -m src.limit_orders BTCUSDT BUY 0.01 50000 --usdt 500
```

### 🔄 Advanced Orders (Programmatic Usage)

```python
from src.config import ConfigManager
from src.logger import BotLogger
from src.validators import TradingValidator
from src.spot_api_client import SpotAPIClient
from src.spot_orders_module import SpotOrderManager

# Initialize for spot trading
config_manager = ConfigManager()
config = config_manager.load_config()
logger = BotLogger(config.log_file, config.log_level)
validator = TradingValidator(logger)
api_client = SpotAPIClient(config.api_key, config.api_secret, config.base_url, logger)
spot_manager = SpotOrderManager(api_client, validator, logger)

# Place spot market order
result = spot_manager.place_market_order_usdt(
    symbol="BTCUSDT",
    side="BUY",
    usdt_amount=10.0
)
```

## 📊 Supported Trading Pairs

### Spot Trading
- BTCUSDT, ETHUSDT, BNBUSDT, ADAUSDT, XRPUSDT
- SOLUSDT, DOTUSDT, DOGEUSDT, AVAXUSDT, MATICUSDT
- LINKUSDT, LTCUSDT, BCHUSDT, UNIUSDT, ATOMUSDT
- And many more available on Binance Spot

### Futures Trading
- All USDT-M Futures pairs supported by Binance

## 📝 Logging

All bot activities are logged to `bot.log` in JSON format:

```json
{
    "timestamp": "2025-08-09T12:35:55.796",
    "level": "INFO",
    "logger": "binance_bot",
    "message": "Spot market order placed successfully - Order ID: 13519607, Executed: 0.00008000"
}
```

### Log Types
- API calls and responses
- Order placements and executions
- Error details and stack traces
- Validation failures
- Bot actions and status updates

## 🏗️ Project Structure

```
python/
├── src/
│   ├── __init__.py
│   ├── config.py                 # Configuration management
│   ├── logger.py                 # Structured logging
│   ├── validators.py             # Input validation
│   │
│   ├── # Spot Trading (Working)
│   ├── spot_api_client.py        # Spot API client
│   ├── spot_orders.py            # Spot market orders CLI
│   ├── spot_limit_orders.py      # Spot limit orders CLI
│   ├── spot_orders_module.py     # Spot order logic
│   │
│   ├── # Futures Trading (Advanced)
│   ├── api_client.py             # Futures API client
│   ├── market_orders.py          # Futures market orders CLI
│   ├── limit_orders.py           # Futures limit orders CLI
│   ├── market_orders_module.py   # Futures market order logic
│   ├── limit_orders_module.py    # Futures limit order logic
│   │
│   └── advanced/                 # Advanced futures strategies
│       ├── __init__.py
│       ├── stop_limit_orders.py  # Stop-limit orders
│       ├── oco.py                # OCO orders
│       ├── twap.py               # TWAP orders
│       └── grid_orders.py        # Grid orders
│
├── bot.log                       # Trading logs
├── config.json                   # Configuration file
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🔧 Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `api_key` | Your Binance API key | Required |
| `api_secret` | Your Binance API secret | Required |
| `use_testnet` | Use testnet for safe testing | `true` |
| `base_url` | API endpoint URL | `https://testnet.binance.vision` |
| `log_file` | Log file location | `bot.log` |
| `log_level` | Logging level | `INFO` |
| `default_leverage` | Default leverage for futures | `1` |
| `max_position_size` | Maximum position size | `1000.0` |
| `request_timeout` | API request timeout (seconds) | `30` |
| `max_retries` | Maximum API retries | `3` |

## 🛡️ Security & Safety

### Testnet First
- ✅ Always test on testnet before using real funds
- ✅ Current configuration is set for testnet by default
- ✅ No real money at risk during testing

### API Security
- 🔐 API keys loaded from secure configuration files
- 🔐 All API requests signed using HMAC SHA256
- 🔐 No sensitive data logged
- 🔐 IP whitelisting support

### Error Handling
- 🛡️ Comprehensive input validation
- 🛡️ Network error recovery with retries
- 🛡️ Rate limiting protection
- 🛡️ Detailed error logging

## 📊 Recent Trading Activity

Based on successful testnet trades:

```
✅ Market Order #13519607: Bought 0.00008 BTC for $10 USDT
✅ Market Order #9838576: Bought 0.00120 ETH for $5 USDT  
✅ Limit Order #13519652: Placed buy order for 0.001 BTC at $50,000
```

## 🚨 Error Handling

The bot includes comprehensive error handling for:

- **Validation Errors**: Invalid parameters with detailed messages
- **API Errors**: Network and Binance API error handling
- **Rate Limiting**: Automatic retry with exponential backoff
- **Connection Errors**: Robust connection handling and recovery
- **Order Errors**: Detailed logging of failed orders

## 📋 Requirements

- Python 3.7+
- requests>=2.25.1
- typing-extensions>=3.7.4

## 🆘 Troubleshooting

### Common Issues

**"Invalid API-key" Error:**
- Verify API keys are correct in `config.json`
- Check if IP address is whitelisted
- Ensure API key has required permissions (spot/futures trading)

**"Insufficient Balance" Error:**
- Add testnet funds from the faucet
- Check if you have enough balance for the order

**"Quantity Must Be At Least" Error:**
- Check minimum order sizes for the trading pair
- Use smaller quantities or USDT amounts

### Getting Help

1. Check the logs in `bot.log` for detailed error information
2. Verify your API credentials and permissions
3. Ensure you're using the correct testnet/mainnet configuration
4. Review the Binance API documentation

## ⚖️ Legal Disclaimer

**This bot is for educational and testing purposes only.**

- 📚 Educational use only - not financial advice
- ⚠️ Trading cryptocurrencies involves significant risk
- 🧪 Always test thoroughly on testnet before using real funds
- 💰 The authors are not responsible for any financial losses
- 📖 Use at your own risk and discretion

## 🔄 Version History

- **v2.0** - Added working spot trading functionality
- **v1.0** - Initial futures trading implementation
- **v1.1** - Added advanced order types (OCO, TWAP, Grid)
- **v1.2** - Enhanced logging and error handling

## 📞 Support

For technical issues:
1. Check logs in `bot.log`
2. Verify API credentials and permissions
3. Test on Binance testnet first
4. Review this documentation

---

**Ready to start trading?** Begin with the spot trading examples above using your testnet API keys! 🚀