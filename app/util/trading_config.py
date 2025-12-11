import configparser
import redis
import mysql.connector
import sys


class Trading_config:

    def __init__(self):
        # read config
        self.config = configparser.ConfigParser()
        self.config.read("conf.ini")
        # self.assets_list = ['ETHEUR', 'ETHUSDT', 'BTCUSDT', 'RADUSDT', 'RVNUSDT', 'UMAUSDT', 'MOVRUSDT', 'PEOPLEUSDT', 'LINKUSDT', 'RAYUSDT', 'INJUSDT']
        # self.assets_list = ['ETHUSDT', 'BTCUSDT', 'RVNUSDT', 'MOVRUSDT', 'PEOPLEUSDT', 'LINKUSDT', 'RAYUSDT', 'INJUSDT']
        # self.assets_list = ['ARUSDT', 'PEOPLEUSDT', 'LDOUSDT', 'AXSUSDT']

        # test data history list
        self.assets_list = ["PYTHUSDT", "ARUSDT"]

    def get_redis(self):
        return redis.Redis(
            host=self.config["REDIS"]["host"],
            port=self.config["REDIS"]["port"],
            db=self.config["REDIS"]["db"],
        )

    def get_assets_matching(self):

        self.assets_matching = {}

        for asset in self.assets_list:

            if "ASSET_SYMBOL_MATCHING_" + asset in self.config.keys():
                matching = self.config["ASSET_SYMBOL_MATCHING_" + asset]
            else:
                matching = self.config["ASSET_SYMBOL_MATCHING_DEFAULT"]

            self.assets_matching[asset] = {
                "FMP": matching["FMP"],
                "kraken": matching["kraken"],
            }
            if "ASSET_SYMBOL_MATCHING_" + asset in self.config.keys():
                self.assets_matching[asset]["binance"] = matching["binance"]
            else:
                self.assets_matching[asset]["binance"] = asset

        return self.assets_matching

    def get_config(self):

        self.kraken_data = self.config["MARKETS_DATA"]["kraken_data"]
        self.FMP_data = self.config["MARKETS_DATA"]["fmp_data"]
        self.binance_data = self.config["MARKETS_DATA"]["binance_data"]
        self.FMP_data_key = self.config["MARKETS_DATA"]["fmp_data_key"]

        self.check_pace_0 = {}
        self.check_pace_1_for_buy_order = {}
        self.check_pace_1_for_short_order = {}

        self.increase_threeshold = {}
        self.decrease_threeshold = {}
        self.increase_threeshold_for_update = {}
        self.decrease_threeshold_for_update = {}
        self.sell_threeshold_before_price_update = {}
        self.sell_threeshold = {}
        self.close_short_sell_threeshold_before_price_update = {}
        self.close_short_sell_threeshold = {}

        self.change_direction_number_allowed_after_buy_order = {}
        self.change_direction_number_allowed_after_short_sell_order = {}

        for asset in self.assets_list:

            if "CHECK_PACE_" + asset in self.config.keys():
                check_pace = self.config["CHECK_PACE_" + asset]
            else:
                check_pace = self.config["CHECK_PACE_DEFAULT"]

            if "TRANSACTIONS_THREESHOLDS_" + asset in self.config.keys():
                transactions_threesholds = self.config[
                    "TRANSACTIONS_THREESHOLDS_" + asset
                ]
            else:
                transactions_threesholds = self.config[
                    "TRANSACTIONS_THREESHOLDS_DEFAULT"
                ]

            self.check_pace_0[asset] = int(check_pace["check_pace_1st_change"])
            self.check_pace_1_for_buy_order[asset] = int(
                check_pace["check_pace_after_1st_change_for_buy_order"]
            )
            self.check_pace_1_for_short_order[asset] = int(
                check_pace["check_pace_after_1st_change_for_short_order"]
            )
            self.increase_threeshold[asset] = float(
                transactions_threesholds["increase_threeshold"]
            )
            self.decrease_threeshold[asset] = float(
                transactions_threesholds["decrease_threeshold"]
            )
            self.increase_threeshold_for_update[asset] = float(
                transactions_threesholds["increase_threeshold_for_update"]
            )
            self.decrease_threeshold_for_update[asset] = float(
                transactions_threesholds["decrease_threeshold_for_update"]
            )
            self.sell_threeshold_before_price_update[asset] = float(
                transactions_threesholds["sell_threeshold_before_price_update"]
            )
            self.sell_threeshold[asset] = float(
                transactions_threesholds["sell_threeshold"]
            )
            self.close_short_sell_threeshold_before_price_update[asset] = float(
                transactions_threesholds[
                    "close_short_sell_threeshold_before_price_update"
                ]
            )
            self.close_short_sell_threeshold[asset] = float(
                transactions_threesholds["close_short_sell_threeshold"]
            )
            self.change_direction_number_allowed_after_buy_order[asset] = int(
                transactions_threesholds[
                    "change_direction_number_allowed_after_buy_order"
                ]
            )
            self.change_direction_number_allowed_after_short_sell_order[asset] = int(
                transactions_threesholds[
                    "change_direction_number_allowed_after_short_sell_order"
                ]
            )

            self.number_open_position_allowed = int(
                self.config["BIN_ACC"]["number_open_position_allowed"]
            )

        return [
            self.check_pace_0,
            self.check_pace_1_for_buy_order,
            self.check_pace_1_for_short_order,
            self.increase_threeshold,
            self.decrease_threeshold,
            self.increase_threeshold_for_update,
            self.decrease_threeshold_for_update,
            self.sell_threeshold_before_price_update,
            self.sell_threeshold,
            self.close_short_sell_threeshold_before_price_update,
            self.close_short_sell_threeshold,
            self.kraken_data,
            self.FMP_data,
            self.binance_data,
            self.FMP_data_key,
            self.change_direction_number_allowed_after_buy_order,
            self.change_direction_number_allowed_after_short_sell_order,
            self.number_open_position_allowed,
        ]
