from gateway import BinanceSpotHttp, OrderStatus, OrderType, OrderSide
from gateway import BinanceFutureHttp
from utils import config
from utils import utility, round_to
from enum import Enum
import logging


class OkexTrader(object):

    def __init__(self):
        """
        :param api_key:
        :param secret:
        :param trade_type: 交易的类型， only support future and spot.
        """
        self.http_client = BinanceSpotHttp(
            api_key=config.api_key, secret=config.secret)

        self.buy_orders = []  # 买单.
        self.sell_orders = []  # 卖单.

    def get_bid_ask_price(self):

        ticker = self.http_client.get_ticker(config.symbol)

        bid_price = 0
        ask_price = 0
        if ticker:
            bid_price = float(ticker.get('bidPrice', 0))
            ask_price = float(ticker.get('askPrice', 0))

        return bid_price, ask_price

    def grid_trader(self):
        """
        执行核心逻辑，网格交易的逻辑.
        :return:
        """

        bid_price, ask_price = self.get_bid_ask_price()
        print(f"bid_price: {bid_price}, ask_price: {ask_price}")

        quantity = round_to(float(config.quantity), float(config.min_qty))

        # 最高价到最低价.
        self.buy_orders.sort(key=lambda x: float(x['price']), reverse=True)
        # 最高价到最低价.
        self.sell_orders.sort(key=lambda x: float(x['price']), reverse=True)
        print(f"buy orders: {self.buy_orders}")
        print("------------------------------")
        print(f"sell orders: {self.sell_orders}")

        buy_delete_orders = []  # 需要删除买单
        sell_delete_orders = []  # 需要删除的卖单

        # 买单逻辑,检查成交的情况.
        for buy_order in self.buy_orders:

            check_order = self.http_client.get_order(buy_order.get(
                'symbol', config.symbol), client_order_id=buy_order.get('clientOrderId'))

            if check_order:
                if check_order.get('status') == OrderStatus.CANCELED.value:
                    buy_delete_orders.append(buy_order)
                    print(
                        f"buy order status was canceled: {check_order.get('status')}")
                elif check_order.get('status') == OrderStatus.FILLED.value:
                    # 买单成交，挂卖单.
                    logging.info(
                        f"买单成交->价格: {check_order.get('price')}, 数量: {check_order.get('origQty')}")

                    sell_price = round_to(float(check_order.get(
                        "price")) * (1 + float(config.gap_percent)), config.min_price)
                    new_sell_order = self.http_client.place_order(
                        symbol=config.symbol, order_side=OrderSide.SELL, order_type=OrderType.LIMIT, quantity=quantity, price=sell_price)
                    if new_sell_order:
                        buy_delete_orders.append(buy_order)
                        self.sell_orders.append(new_sell_order)

                    buy_price = round_to(float(check_order.get("price")) * (1 - float(config.gap_percent)),
                                         config.min_price)
                    new_buy_order = self.http_client.place_order(
                        symbol=config.symbol, order_side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=quantity, price=buy_price)
                    if new_buy_order:
                        self.buy_orders.append(new_buy_order)

                elif check_order.get('status') == OrderStatus.NEW.value:
                    print("buy order status is: New")
                else:
                    print(
                        f"buy order status is not above options: {check_order.get('status')}")

        # 过期或者拒绝的订单删除掉.
        for delete_order in buy_delete_orders:
            self.buy_orders.remove(delete_order)

        # 卖单逻辑, 检查卖单成交情况.
        for sell_order in self.sell_orders:

            check_order = self.http_client.get_order(sell_order.get('symbol', config.symbol),
                                                     client_order_id=sell_order.get('clientOrderId'))
            if check_order:
                if check_order.get('status') == OrderStatus.CANCELED.value:
                    sell_delete_orders.append(sell_order)

                    print(
                        f"sell order status was canceled: {check_order.get('status')}")
                elif check_order.get('status') == OrderStatus.FILLED.value:
                    logging.info(
                        f"卖单成交->价格: {check_order.get('price')}, 数量: {check_order.get('origQty')}")

                    # 卖单成交，先下买单.
                    buy_price = round_to(float(check_order.get(
                        "price")) * (1 - float(config.gap_percent)), float(config.min_price))
                    new_buy_order = self.http_client.place_order(symbol=config.symbol, order_side=OrderSide.BUY,
                                                                 order_type=OrderType.LIMIT, quantity=quantity, price=buy_price)
                    if new_buy_order:
                        sell_delete_orders.append(sell_order)
                        self.buy_orders.append(new_buy_order)

                    sell_price = round_to(float(check_order.get(
                        "price")) * (1 + float(config.gap_percent)), float(config.min_price))
                    new_sell_order = self.http_client.place_order(symbol=config.symbol, order_side=OrderSide.SELL,
                                                                  order_type=OrderType.LIMIT, quantity=quantity,
                                                                  price=sell_price)
                    if new_sell_order:
                        self.sell_orders.append(new_sell_order)

                elif check_order.get('status') == OrderStatus.NEW.value:
                    print("sell order status is: New")
                else:
                    print(
                        f"sell order status is not in above options: {check_order.get('status')}")

        # 过期或者拒绝的订单删除掉.
        for delete_order in sell_delete_orders:
            self.sell_orders.remove(delete_order)

        # 没有买单的时候.
        if len(self.buy_orders) <= 0:
            if bid_price > 0:
                price = round_to(
                    bid_price * (1 - float(config.gap_percent)), float(config.min_price))
                buy_order = self.http_client.place_order(
                    symbol=config.symbol, order_side=OrderSide.BUY, order_type=OrderType.LIMIT, quantity=quantity, price=price)
                if buy_order:
                    self.buy_orders.append(buy_order)
        elif len(self.buy_orders) > int(config.max_orders):  # 最多允许的挂单数量.
            # 订单数量比较多的时候.
            self.buy_orders.sort(key=lambda x: float(
                x['price']), reverse=False)  # 最低价到最高价

            delete_order = self.buy_orders[0]
            order = self.http_client.cancel_order(delete_order.get(
                'symbol'), client_order_id=delete_order.get('clientOrderId'))
            if order:
                self.buy_orders.remove(delete_order)

        # 没有卖单的时候.
        if len(self.sell_orders) <= 0:
            if ask_price > 0:
                price = round_to(
                    ask_price * (1 + float(config.gap_percent)), float(config.min_price))
                order = self.http_client.place_order(
                    symbol=config.symbol, order_side=OrderSide.SELL, order_type=OrderType.LIMIT, quantity=quantity, price=price)
                if order:
                    self.sell_orders.append(order)

        elif len(self.sell_orders) > int(config.max_orders):  # 最多允许的挂单数量.
            # 订单数量比较多的时候.
            self.sell_orders.sort(
                key=lambda x: x['price'], reverse=True)  # 最高价到最低价

            delete_order = self.sell_orders[0]
            order = self.http_client.cancel_order(delete_order.get('symbol'),
                                                  client_order_id=delete_order.get('clientOrderId'))
            if order:
                self.sell_orders.remove(delete_order)
