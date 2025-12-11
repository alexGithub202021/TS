from util.functions import Functions
from binance.client import Client
from urllib.parse import urlencode
import hmac
import time
import hashlib
import requests
import configparser
import json
import math
import sys

config = configparser.ConfigParser()
config.read("conf.ini")

api_url = config["BIN_ACC"]["url"]
api_key = config["BIN_ACC"]["key"]
api_sec = config["BIN_ACC"]["secret"]
investment_amount = config["BIN_ACC"]["amount"]


class Binance_api:

    def __init__(self):
        self.client = Client(api_key, api_sec)

    def hashing(self, query_string):
        return hmac.new(
            api_sec.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

    def get_timestamp(
        self,
    ):
        return int(time.time() * 1000)

    # used for sending request requires the signature
    def send_signed_request(self, http_method, url_path, payload={}):

        query_string = urlencode(payload, True)
        if query_string:
            query_string = "{}&timestamp={}".format(query_string, self.get_timestamp())
        else:
            query_string = "timestamp={}".format(self.get_timestamp())

        url = (
            api_url
            + url_path
            + "?"
            + query_string
            + "&signature="
            + self.hashing(query_string)
        )

        headers = {}
        headers["Content-Type"] = "application/json;charset=utf-8"
        headers["X-MBX-APIKEY"] = api_key

        if "GET" == http_method:
            response = requests.get((url), headers=headers)
        if "POST" == http_method:
            response = requests.post((url), headers=headers)

        return response

    """ _summary_: step_size is used to set the accuracy of the qty trade
        Raises:
            Exception: is resp status != 200
        Returns:
            _type_: string
    """

    def get_step_size(self, asset, logger):

        url = f"https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(url)

        if not response.status_code == 200:
            logger.info(
                Functions().get_date()
                + "(exchangeInfo status: "
                + str(response.status_code)
                + ")"
            )
            print("(exchangeInfo status: " + str(response.status_code) + ")")
            raise Exception("exchangeInfo Status " + str(response.status_code))
        else:
            logger.info(
                Functions().get_date()
                + "(exchangeInfo status: "
                + str(response.status_code)
                + ")"
            )
            print("(exchangeInfo status: " + str(response.status_code) + ")")
            data = response.json()

            for symbol_info in data["symbols"]:
                if asset in symbol_info["symbol"]:
                    filters = symbol_info["filters"]
                    for filter in filters:
                        if filter["filterType"] == "LOT_SIZE":
                            return filter["stepSize"]

    # *** todo extract sub methods ***
    def binance_order(self, asset_data, order, logger, redis):

        # *** 'buy' or 'short sell' order ***
        if "buy" == order or "short sell" == order:
            self.open_position(asset_data, order, redis, logger)

        # *** 'sell' or 'close short sell' order ***
        if "close short sell" == order or "sell" == order:
            self.close_position(asset_data, order, logger)

    def close_position(self, asset_data, order, logger):

        volume = self.get_volume_from_account_balance(asset_data, order, logger)

        if "sell" == order:
            self.sell_position(asset_data["name"], order, volume, logger)

        if "close short sell" == order:
            self.close_short_sell_position(asset_data["name"], order, volume, logger)

    def close_short_sell_position(self, asset_name, order, volume, logger):

        response = self.client.create_margin_order(
            symbol=asset_name,
            isIsolated="FALSE",
            side="BUY",
            type="MARKET",
            quantity=volume,
            sideEffectType="AUTO_REPAY",
        )
        if "FILLED" != response["status"]:
            logger.info(
                Functions().get_date()
                + order
                + " "
                + asset_name
                + ", status failed,  "
                + " ,msg: "
                + str(response)
            )
            print(
                ">>> "
                + order
                + " "
                + asset_name
                + ", status failed,  "
                + " ,msg: "
                + str(response)
            )
            raise Exception("error response msg: " + str(response))
        else:
            logger.info(
                Functions().get_date()
                + "("
                + order
                + " status: "
                + str(response["status"])
                + ")"
            )
            print(
                ">>> ("
                + order
                + " "
                + asset_name
                + ", status: "
                + str(response["status"])
                + ")"
            )
            return

    def sell_position(self, asset_name, order, volume, logger):

        url_path = "/api/v3/order"
        params = {
            "symbol": asset_name,
            "side": order,
            "type": "MARKET",
            "quantity": volume,
        }
        response = self.send_signed_request("POST", url_path, params)

        if not response.status_code == 200:
            logger.exception(
                Functions().get_date()
                + "Status "
                + str(response.status_code)
                + ", "
                + order
                + " order failed"
            )
            print(
                ">>> ("
                + order
                + " "
                + asset_name
                + ", status: "
                + str(response.status_code)
                + ")"
            )
            raise Exception("Status " + str(response.status_code))
        else:
            logger.info(
                Functions().get_date()
                + "("
                + order
                + " status: "
                + str(response.status_code)
                + ")"
            )
            print(
                ">>> ("
                + order
                + " "
                + asset_name
                + ", status: "
                + str(response.status_code)
                + ")"
            )

    def get_volume_from_account_balance(self, asset_data, order, logger):

        # *** get volume fr acc balance ***
        if "sell" == order:
            response = self.send_signed_request("GET", "/api/v3/account")
            content = "balances"
            volume_from_acc_balance = "free"

        if "close short sell" == order:
            response = self.send_signed_request("GET", "/sapi/v1/margin/account")
            content = "userAssets"
            volume_from_acc_balance = "borrowed"

        if not response.status_code == 200:
            print("(account balance status: " + str(response.status_code) + ")")
            logger.info("(account balance status: " + str(response.status_code) + ")")
            raise Exception("Status " + str(response.status_code))
        else:
            logger.info(
                Functions().get_date()
                + "(GET /sapi/v1/margin/account > status: "
                + str(response.status_code)
                + ")"
            )
            response_content = json.loads(str(response.content.decode()))[content]

            for asset in response_content:
                if asset["asset"] == asset_data["name"][:-4]:
                    step_size = self.get_step_size(asset_data["name"], logger)
                    volume = round(
                        math.floor(
                            float(asset[volume_from_acc_balance])
                            * (1 / float(step_size))
                        )
                        / (1 / float(step_size)),
                        8,
                    )

                    print(
                        "volume fr account balance for "
                        + asset_data["name"]
                        + " "
                        + order
                        + ": "
                        + str(volume)
                    )
                    return volume

            print("asset " + asset_data["name"] + " not found in account balance")
            logger.info(
                Functions().get_date()
                + "asset "
                + asset_data["name"]
                + " not found in account balance"
            )
            raise Exception("Status " + str(response.status_code))

    def open_position(self, asset_data, order, redis, logger):

        volume = self.get_volume(asset_data, order, redis, logger)

        if "buy" == order:
            self.buy_asset(asset_data["name"], order, volume, logger)

        if "short sell" == order:
            self.short_sell_asset(asset_data["name"], order, volume, logger)

    def get_volume(self, asset_data, order, redis, logger):

        volume = round(
            float(investment_amount) / float(asset_data["price_reference"]), 8
        )
        step_size = self.get_step_size(asset_data["name"], logger)
        volume = round(round(volume / float(step_size)) * float(step_size), 8)
        print(
            "volume for " + order + ": ",
            str(volume) + ", @price: " + str(asset_data["price_reference"]),
        )
        asset_data["volume"] = volume
        redis.set(asset_data["name"] + ":volume", volume)

        return volume

    def short_sell_asset(self, asset_name, order, volume, logger):

        response = self.client.create_margin_order(
            symbol=asset_name,
            isIsolated="FALSE",
            side="SELL",
            type="MARKET",
            quantity=volume,
            sideEffectType="MARGIN_BUY",
        )
        # print(response['status'])
        if "FILLED" != response["status"]:
            logger.info(
                Functions().get_date()
                + order
                + " "
                + asset_name
                + ", status failed,  "
                + " ,msg: "
                + str(response)
            )
            print(
                ">>> "
                + order
                + " "
                + asset_name
                + ", status failed,  "
                + " ,msg: "
                + str(response)
            )
            raise Exception("error response msg: " + str(response))
        else:
            logger.info(
                Functions().get_date()
                + "("
                + order
                + " status: "
                + str(response["status"])
                + ")"
            )
            print(
                ">>> ("
                + order
                + " "
                + asset_name
                + ", status: "
                + str(response["status"])
                + ")"
            )
            return

    def buy_asset(self, asset_name, order, volume, logger):

        url_path = "/api/v3/order"
        params = {
            "symbol": asset_name,
            "side": order,
            "type": "MARKET",
            "quantity": volume,
        }
        response = self.send_signed_request("POST", url_path, params)

        if not response.status_code == 200:
            logger.exception(
                Functions().get_date()
                + "Status "
                + str(response.status_code)
                + ", "
                + order
                + " order failed"
            )
            print(
                ">>> ("
                + order
                + " "
                + asset_name
                + ", status: "
                + str(response.status_code)
                + ")"
            )
            raise Exception("Status " + str(response.status_code))
        else:
            logger.info(
                Functions().get_date()
                + "("
                + order
                + " status: "
                + str(response.status_code)
                + ")"
            )
            print(
                ">>> ("
                + order
                + " "
                + asset_name
                + ", status: "
                + str(response.status_code)
                + ")"
            )
