import logging
import time

from trader.binance_trader import BinanceTrader
from utils import config

format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=format,
                    filename='grid_trader_log.txt')
logger = logging.getLogger('binance')

if __name__ == '__main__':
    config.loads('./config.json')
    config.loads('./.credentials.json')
    binance_trader = BinanceTrader()
    orders = binance_trader.http_client.cancel_open_orders(config.symbol)
    print(f"cancel orders: {orders}")

while True:
    try:
        binance_trader.grid_trader()
        time.sleep(10)

    except Exception as error:
        print(f"catch error: {error}")
        time.sleep(60)
