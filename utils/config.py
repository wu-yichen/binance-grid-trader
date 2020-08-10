# -*- coding:utf-8 -*-
import json


class Config:

    def __init__(self):

        self.platform: str = "binance_spot"  # 交易的平台
        self.symbol: str = "BNBUSDT"  # 交易对.
        self.gap_percent: float = 0.01  # 网格变化交易的单位.
        self.api_key: str = None
        self.secret: str = None
        self.pass_phrase = None
        self.quantity: float = 1
        self.min_price = 0.0001
        self.min_qty = 0.01
        self.max_orders = 1

    def loads(self, config_file=None):
        """ Load config file.

        Args:
            config_file: config json file.
        """
        configures = {}
        if config_file:
            try:
                with open(config_file) as f:
                    data = f.read()
                    configures = json.loads(data)
            except Exception as e:
                print(e)
                exit(0)
            if not configures:
                print("config json file error!")
                exit(0)
        self._update(configures)

    def _update(self, update_fields):
        """
        更新update fields.
        :param update_fields:
        :return: None

        """

        for k, v in update_fields.items():
            setattr(self, k, v)


config = Config()
