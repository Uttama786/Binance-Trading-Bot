#!/usr/bin/env python3
"""
Spot Orders CLI Entry Point for Testnet

Usage:
    python -m src.spot_orders <symbol> <side> <quantity>
    python -m src.spot_orders BTCUSDT BUY 0.01
    python -m src.spot_orders ETHUSDT SELL 0.1
"""

import sys
import argparse
from .config import ConfigManager
from .logger import BotLogger
from .validators import TradingValidator
from .spot_api_client import SpotAPIClient
from .spot_orders_module import SpotOrderManager


def main():
    parser = argparse.ArgumentParser(description='Binance Spot Order Bot (Testnet)')
    parser.add_argument('symbol', help='Trading symbol (e.g., BTCUSDT)')
    parser.add_argument('side', choices=['BUY', 'SELL'], help='Order side')
    parser.add_argument('quantity', type=float, help='Order quantity or USDT amount')
    parser.add_argument('--usdt', action='store_true', help='Quantity is in USDT (quoteOrderQty)')
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Initialize components
        logger = BotLogger(config.log_file, config.log_level)
        validator = TradingValidator(logger)
        api_client = SpotAPIClient(config.api_key, config.api_secret, config.base_url, logger)
        spot_manager = SpotOrderManager(api_client, validator, logger)
        
        # Place order
        if args.usdt:
            result = spot_manager.place_market_order_usdt(
                symbol=args.symbol,
                side=args.side,
                usdt_amount=args.quantity
            )
        else:
            result = spot_manager.place_market_order(
                symbol=args.symbol,
                side=args.side,
                quantity=args.quantity
            )
        
        print(f"✅ Spot order placed successfully!")
        print(f"Order ID: {result.get('orderId')}")
        print(f"Status: {result.get('status')}")
        print(f"Executed Qty: {result.get('executedQty')}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
