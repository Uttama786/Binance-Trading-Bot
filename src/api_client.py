"""
API Client module for Binance Futures Trading Bot
Handles all API interactions with Binance Futures
"""

import time
import hmac
import hashlib
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode
from .logger import BotLogger


class BinanceAPIClient:
    """Main API client for Binance Futures"""
    
    def __init__(self, api_key: str, api_secret: str, base_url: str = "https://testnet.binancefuture.com", logger: BotLogger = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.logger = logger or BotLogger()
        self.session = requests.Session()
        self.session.headers.update({
            'X-MBX-APIKEY': self.api_key,
            'Content-Type': 'application/json'
        })
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for authenticated requests"""
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict[str, Any] = None, 
                     signed: bool = False) -> Dict[str, Any]:
        """Make HTTP request to Binance API with logging and error handling"""
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        # Add timestamp for signed requests
        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        start_time = time.time()
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(url, params=params, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response_time_ms = (time.time() - start_time) * 1000
            
            # Log API call
            self.logger.log_api_call(
                endpoint=endpoint,
                method=method,
                params=params,
                status_code=response.status_code,
                response_time_ms=response_time_ms
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json() if response.content else {'msg': 'Unknown error'}
                self.logger.log_error(
                    error_type="API_ERROR",
                    message=error_data.get('msg', 'Unknown API error'),
                    endpoint=endpoint,
                    status_code=response.status_code,
                    error_code=error_data.get('code')
                )
                raise Exception(f"API Error {response.status_code}: {error_data.get('msg', 'Unknown error')}")
                
        except requests.exceptions.RequestException as e:
            response_time_ms = (time.time() - start_time) * 1000
            self.logger.log_error(
                error_type="NETWORK_ERROR",
                message=str(e),
                endpoint=endpoint,
                method=method
            )
            raise Exception(f"Network error: {str(e)}")
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_position_risk(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get position risk information"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/fapi/v2/positionRisk', params, signed=True)
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange information"""
        return self._make_request('GET', '/fapi/v1/exchangeInfo')
    
    def get_symbol_info(self, symbol: str) -> Dict[str, Any]:
        """Get symbol information"""
        exchange_info = self.get_exchange_info()
        for symbol_info in exchange_info['symbols']:
            if symbol_info['symbol'] == symbol:
                return symbol_info
        raise ValueError(f"Symbol {symbol} not found")
    
    def get_mark_price(self, symbol: str) -> Dict[str, Any]:
        """Get mark price for a symbol"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/fapi/v1/premiumIndex', params)
    
    def get_ticker_price(self, symbol: str) -> Dict[str, Any]:
        """Get current ticker price"""
        params = {'symbol': symbol}
        return self._make_request('GET', '/fapi/v1/ticker/price', params)
    
    def get_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> List[List]:
        """Get kline/candlestick data"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/klines', params)
    
    def place_market_order(self, symbol: str, side: str, quantity: float, 
                          reduce_only: bool = False) -> Dict[str, Any]:
        """Place a market order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': quantity,
            'reduceOnly': reduce_only
        }
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float,
                         time_in_force: str = 'GTC', reduce_only: bool = False) -> Dict[str, Any]:
        """Place a limit order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'LIMIT',
            'timeInForce': time_in_force,
            'quantity': quantity,
            'price': price,
            'reduceOnly': reduce_only
        }
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def place_stop_market_order(self, symbol: str, side: str, quantity: float, 
                               stop_price: float, reduce_only: bool = False) -> Dict[str, Any]:
        """Place a stop market order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'STOP_MARKET',
            'quantity': quantity,
            'stopPrice': stop_price,
            'reduceOnly': reduce_only
        }
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def place_stop_limit_order(self, symbol: str, side: str, quantity: float, 
                              price: float, stop_price: float, time_in_force: str = 'GTC',
                              reduce_only: bool = False) -> Dict[str, Any]:
        """Place a stop limit order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'STOP_LIMIT',
            'timeInForce': time_in_force,
            'quantity': quantity,
            'price': price,
            'stopPrice': stop_price,
            'reduceOnly': reduce_only
        }
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def place_take_profit_market_order(self, symbol: str, side: str, quantity: float,
                                      stop_price: float, reduce_only: bool = False) -> Dict[str, Any]:
        """Place a take profit market order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'TAKE_PROFIT_MARKET',
            'quantity': quantity,
            'stopPrice': stop_price,
            'reduceOnly': reduce_only
        }
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def place_take_profit_limit_order(self, symbol: str, side: str, quantity: float,
                                     price: float, stop_price: float, time_in_force: str = 'GTC',
                                     reduce_only: bool = False) -> Dict[str, Any]:
        """Place a take profit limit order"""
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'TAKE_PROFIT_LIMIT',
            'timeInForce': time_in_force,
            'quantity': quantity,
            'price': price,
            'stopPrice': stop_price,
            'reduceOnly': reduce_only
        }
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def place_oco_order(self, symbol: str, side: str, quantity: float,
                       price: float, stop_price: float, stop_limit_price: float,
                       stop_limit_time_in_force: str = 'GTC') -> Dict[str, Any]:
        """Place an OCO (One-Cancels-the-Other) order"""
        params = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': price,
            'stopPrice': stop_price,
            'stopLimitPrice': stop_limit_price,
            'stopLimitTimeInForce': stop_limit_time_in_force
        }
        return self._make_request('POST', '/fapi/v1/order/oco', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Cancel an order"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('DELETE', '/fapi/v1/order', params, signed=True)
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """Cancel all open orders for a symbol"""
        params = {'symbol': symbol}
        return self._make_request('DELETE', '/fapi/v1/allOpenOrders', params, signed=True)
    
    def get_open_orders(self, symbol: str = None) -> List[Dict[str, Any]]:
        """Get open orders"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/fapi/v1/openOrders', params, signed=True)
    
    def get_order_status(self, symbol: str, order_id: int) -> Dict[str, Any]:
        """Get order status"""
        params = {
            'symbol': symbol,
            'orderId': order_id
        }
        return self._make_request('GET', '/fapi/v1/order', params, signed=True)
    
    def get_trade_history(self, symbol: str, limit: int = 500) -> List[Dict[str, Any]]:
        """Get trade history"""
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._make_request('GET', '/fapi/v1/userTrades', params, signed=True)
    
    def change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """Change leverage for a symbol"""
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._make_request('POST', '/fapi/v1/leverage', params, signed=True)
    
    def change_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """Change margin type (ISOLATED or CROSSED)"""
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        return self._make_request('POST', '/fapi/v1/marginType', params, signed=True)
    
    def get_balance(self) -> List[Dict[str, Any]]:
        """Get account balance"""
        return self._make_request('GET', '/fapi/v2/balance', signed=True)
