# from kraken.kraken_api import Kraken_api
from bin.binance_api import Binance_api
from logging.handlers import RotatingFileHandler
from util.trading_config import Trading_config
from util.functions import Functions
import asyncio
import logging
import time
import requests
import sys
import multiprocessing
import csv

# Define a class that contains the user API methods
class Trading_app:

    # Constructor
    def __init__(self):
        
        ### used for test data history
        self.redis = Trading_config().get_redis()
        self.config = Trading_config().get_config()
        self.assets_matching = Trading_config().get_assets_matching()
        
        self.check_pace_0 = self.config[0]
        self.check_pace_1_for_buy_order = self.config[1] 
        self.check_pace_1_for_short_order = self.config[2] 
        self.increase_threeshold = self.config[3] 
        self.decrease_threeshold = self.config[4] 
        self.increase_threeshold_for_update = self.config[5] 
        self.decrease_threeshold_for_update = self.config[6] 
        self.sell_threeshold_before_price_update = self.config[7] 
        self.sell_threeshold = self.config[8] 
        self.close_short_sell_threeshold_before_price_update = self.config[9] 
        self.close_short_sell_threeshold = self.config[10] 
        
        self.kraken_data = self.config[11]
        self.FMP_data = self.config[12]
        self.binance_data = self.config[13]
        self.FMP_data_key = self.config[14]
        
        self.change_direction_number_allowed_after_buy_order = self.config[15]
        self.change_direction_number_allowed_after_short_sell_order = self.config[16]
        
        self.number_open_position_allowed = self.config[17]
        
        if self.redis.exists('counter_open_position'): # retrieve data fr redis collection if exists
            self.counter_open_position = int(self.redis.get('counter_open_position').decode())
        else:                  
            self.counter_open_position = 0
            

    async def run(self):
        
        assets_list = self.get_assets_list()
        
        processes = []
        for asset_data in assets_list:
            process = multiprocessing.Process(target=self.launch_trade, args=[asset_data.copy()])
            processes.append(process)
            process.start()
            
        # Wait for all processes to finish
        for process in processes:
            process.join()
        
    
    """ _summary_: return the new asset price from the market
        returns:
            float: price
    """    
    def market_data(self, asset_data, logger):
        
        #kraken data
        if "kraken" == asset_data['market_api']:
            url = self.kraken_data + '?pair=' +  str(self.assets_matching[asset_data['name']]['kraken'])
        if "binance" == asset_data['market_api']:
            url = self.binance_data + str(self.assets_matching[asset_data['name']]['binance'])
        if "fmp" == asset_data['market_api']:
            url = self.kraken_data + '?pair=' +  str(self.assets_matching[asset_data['name']]['FMP'])
            # url = FMP_data + str(asset_data['name']) + '?apikey=' + FMP_data_key
            
        payload = headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        if not response.status_code == 200:
            logger.exception(Functions().get_date() + ' Status ' + str(response.status_code) + ', ' + str(response.content))
            raise Exception('Status '+ str(response.status_code))
        else:
            
            if "kraken" == asset_data['market_api']:
                new_asset_data = response.json()['result']
                price = new_asset_data[self.assets_matching[asset_data['name']]['kraken']]['c'][0]
            if "binance" == asset_data['market_api']:
                new_asset_data = response.json()
                price = new_asset_data['price']
            if "fmp" == asset_data['market_api']:
                new_asset_data = response.json()[0]
                price = new_asset_data['price']
                
            return float(price)


    """ _summary_: call the api to make the transaction depending on the order (buy, sell, short sell, close short sell)
    """
    def market_order(self, asset_data, order, logger):
        
        # *** biance api ***
        Api = Binance_api()
        Api.binance_order(asset_data, order, logger, self.redis)
        
        if "sell" == order or "close short sell" == order:
            logger.info(Functions().get_date() + 'order ' +  order.upper() + ' finished, @price: ' + str(asset_data['price_reference']) + '\n')
            order = "close"
            self.counter_open_position -= 1
            del asset_data['open_price']
            self.redis.delete(asset_data["name"] + ':open_price')
            
        else:
            logger.info(Functions().get_date() + 'order ' +  order.upper() + ' finished, @price: ' + str(asset_data['price_reference']))
            self.counter_open_position += 1
            asset_data['open_price'] = asset_data['price_reference']
            self.redis.set(asset_data["name"] + ':open_price', asset_data['open_price'])
            
        self.redis.set('counter_open_position', self.counter_open_position)          
        logger.info(Functions().get_date() + 'counter_open_position: ' + str(self.counter_open_position))
            
        asset_data['position'] = order
        self.redis.set(asset_data["name"] + ':position', order)
        
    
    """ _summary_: return the percentage of change between the new asset price and the previous asset reference price
        returns:
            float: percentage delta
    """
    def get_percentage_change(self, asset_data, logger):        
        new_asset_price = self.market_data(asset_data, logger)
        coeff_delta = float(new_asset_price) / float(asset_data['price_reference'])
        percentage_change = coeff_delta * 100 - 100
        return {'new_asset_price': new_asset_price, 'percentage_change': percentage_change}
    
    
    """
        formule de la dérivée approximative (fonction de courbe non connue) -> Différence Finie Arrière:
        
            D = (Yi - Y(i-1)) / (Xi - X(i-1))
            
            Y: asset price
            X: timestamp
            i: instant i
            i-1: i - 1 second
        
    """""    
    def get_derivate(self, asset_data, asset_price):
        unix_timestamp = time.time()
        derivate = (asset_price - asset_data['price_reference']) / (unix_timestamp - (unix_timestamp - 1))
        return derivate
    
    
    """ _summary_: update the asset price used as the reference to monitor the changes
    """
    def update_asset_reference_price(self, new_price, asset_data, logger):
        asset_data['price_reference'] = new_price
        self.redis.set(asset_data["name"] + ':price_reference', asset_data['price_reference'])
        logger.info(Functions().get_date() + asset_data["name"] + ' new price_reference: ' + str(asset_data['price_reference']))
        

    """ _summary_: get assets list fr csv file (db dump, the choice of the csv file format is based on resource consumption optimization)
        returns: 
            dict: assets list, contains the list of assets to be trade
    """
    def get_assets_list(self):
        
        # self.flush_redis()
        
        asset_data = {}
        assets_list = []
        
        with open('assets_list.csv', 'r') as line:
            
            csv_reader = csv.reader(line)
            line_counter=0
            
            print('\n')
            print(Functions().get_date())
            print('# *********************************')
            print('# *** redis collections listing ***')
            print('# *********************************')
            
            if self.redis.get('counter_open_position'):
                print(self.redis.get('counter_open_position').decode())      
            
            for line in csv_reader:
                
                row = [cell.rstrip('\n') for cell in line] # remove \n from the end of the row
                
                if 1 <= line_counter:
                    
                    if self.redis.exists(row[1].strip('"')+':name'): # retrieve data fr redis collection if exists
                        self.get_redis_collection(asset_data, assets_list, row)
                    
                    else:
                        self.create_redis_collection(asset_data, assets_list, row)
                
                    self.print_redis_collection_details(row)
                    
                line_counter+=1
        
        return assets_list
    
    
    def get_redis_collection(self, asset_data, assets_list, row):
        print('\n')
        print('redis collection found for: ' + row[1].strip('"'))
        asset_data['name'] = self.redis.get(row[1].strip('"')+':name').decode()
        asset_data['type'] = self.redis.get(row[1].strip('"')+':type').decode()
        asset_data['market'] = self.redis.get(row[1].strip('"')+':market').decode()
        asset_data['market_api'] = self.redis.get(row[1].strip('"')+':market_api').decode()
        asset_data['position'] = self.redis.get(row[1].strip('"')+':position').decode()
        if self.redis.get(row[1].strip('"')+':price_reference'):
            asset_data['price_reference'] = float(self.redis.get(row[1].strip('"')+':price_reference').decode())
        if self.redis.get(row[1].strip('"')+':volume'):
            asset_data['volume'] = float(self.redis.get(row[1].strip('"')+':volume').decode())
        if self.redis.get(row[1].strip('"')+':open_price'):
            asset_data['open_price'] = float(self.redis.get(row[1].strip('"')+':open_price').decode())
            
        assets_list.append(asset_data.copy()) 
        
        
    def create_redis_collection(self, asset_data, assets_list, row):       
        print('\n')
        print('redis collection creation for: ' + row[1].strip('"'))
        asset_data['name'] = row[1].strip('"')
        asset_data['type'] = row[2].strip('"')
        asset_data['market'] = row[3].strip('"')
        asset_data['market_api'] = row[4].strip('"')
        asset_data['position'] = 'close'
        self.redis.set(row[1].strip('"')+':name', row[1].strip('"'))
        self.redis.set(row[1].strip('"')+':type', row[2].strip('"'))
        self.redis.set(row[1].strip('"')+':market', row[3].strip('"'))
        self.redis.set(row[1].strip('"')+':market_api', row[4].strip('"'))
        self.redis.set(row[1].strip('"')+':position', 'close')
        
        assets_list.append(asset_data.copy())   
        
        
    def print_redis_collection_details(self, row):
        print('# *** Details: ')
        if self.redis.get(row[1].strip('"')+':name'):
            print('name: ' + self.redis.get(row[1].strip('"')+':name').decode())
            print('type: ' + self.redis.get(row[1].strip('"')+':type').decode())
            if self.redis.get('price_reference: ' + row[1].strip('"')+':price_reference'):
                print(self.redis.get(row[1].strip('"')+':price_reference').decode())
            print('market: ' + self.redis.get(row[1].strip('"')+':market').decode())
            print('market_api: ' + self.redis.get(row[1].strip('"')+':market_api').decode())
            if self.redis.get(row[1].strip('"')+':position'):
                print('position: ' + self.redis.get(row[1].strip('"')+':position').decode())
            if self.redis.get(row[1].strip('"')+':price_reference'):
                print('price_reference: ' + self.redis.get(row[1].strip('"')+':price_reference').decode())
            if self.redis.get(row[1].strip('"')+':volume'):
                print('volume: ' + self.redis.get(row[1].strip('"')+':volume').decode())
            if self.redis.get(row[1].strip('"')+':open_price'):
                print('open_price: ' + self.redis.get(row[1].strip('"')+':open_price').decode()) 


    def flush_redis(self):
        self.redis.flushdb() # -> del all redis collections
        sys.exit()


    """ _summary_: contains the main BL about the assets trading
        return: 
            dict: asset_data, infos about the asset in trade
    """
    async def trade(self, asset_data):
        
        logger = self.set_logger(asset_data['name'])
        
        logger.info('\n')
        logger.info('#####################################')
        logger.info(Functions().get_date() + 'begin trade for ' + asset_data['name'])
        logger.info(Functions().get_date() + 'counter_open_position: ' + str(self.counter_open_position))
        
        # *** 1st pull fr market ***
        asset_data['price_reference'] = self.market_data(asset_data, logger)
        logger.info(Functions().get_date() + asset_data['name'] + ' price_reference:' + str(asset_data['price_reference']))
        
        # **** tests basics
        # await self.test_basic_operations(asset_data, logger)
        # return
        # self.test_config(asset_data)
        # return
        # **** fin tests
        
        while True:
        
            await self.delay_when_no_open_position(self.check_pace_0[asset_data['name']])
            
            data = self.get_percentage_change(asset_data, logger)
            
            if self.counter_open_position <= self.number_open_position_allowed:
            
                if data['percentage_change'] > self.increase_threeshold[asset_data['name']] and "close" == asset_data["position"]:
                    self.launch_initial_order('buy', data['percentage_change'], data['new_asset_price'], asset_data, logger)

                if data['percentage_change'] < self.decrease_threeshold[asset_data['name']] and "close" == asset_data["position"] and "crypto_half" != asset_data["type"]:
                    self.launch_initial_order('short sell', data['percentage_change'], data['new_asset_price'], asset_data, logger)

                # this counter is defined for each asset/process
                counter = {
                    'before_price_update': True
                }

                # *** monitoring changes when position open (buy or short sell) ***
                while "close" != asset_data["position"]:
                    
                    if 'buy' == asset_data['position']:
                        pace = self.check_pace_1_for_buy_order[asset_data['name']]
                    if 'short sell' == asset_data['position']:
                        pace = self.check_pace_1_for_short_order[asset_data['name']]
                    
                    await self.delay_when_position_is_open(pace)
                    
                    data = self.get_percentage_change(asset_data, logger)
                    
                    if "buy" == asset_data["position"]:
                        self.handle_sell_order(data['percentage_change'], data['new_asset_price'], asset_data, logger, counter)

                    if "short sell" == asset_data["position"]:
                        self.handle_close_short_sell_order(data['percentage_change'], data['new_asset_price'], asset_data, logger, counter)
        
        
    """ _summary_: enable the use of async functions in multiprocessing (parallelism) context
        return: 
            dict: asset_data, infos about the asset in trade
    """
    def launch_trade(self, asset_data):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.trade(asset_data))
        
        
    async def test_basic_operations(self, asset_data, logger):
        self.market_order(asset_data, "buy", logger)
        await asyncio.sleep(5)
        self.market_order(asset_data, "sell", logger)
        await asyncio.sleep(10)
        self.market_order(asset_data, "short sell", logger)
        await asyncio.sleep(5)
        self.market_order(asset_data, "close short sell", logger)
        
    
    def test_config(self):
        i=0
        while i < len(self.config):
            print(type(self.config[i]['ETHEUR']))
            i+=1
        

    def launch_initial_order(self, order, percentage_change, new_asset_price, asset_data, logger):
        logger.info(Functions().get_date() + 'Launch order "' + order + '" for ' + asset_data['name'] + ', percentage_change: ' + str(percentage_change))
        self.update_asset_reference_price(new_asset_price, asset_data, logger)
        self.market_order(asset_data, order, logger)    
        
        
    def set_logger(self, asset_name):
        file1 = 'logs/' + asset_name + '_log_short.log'
        file2 = 'logs/' + asset_name + '_log_long.log'
        
        handler = RotatingFileHandler(filename=file1, maxBytes=500*1024)
        logger = multiprocessing.get_logger()
        logger.addHandler(handler)
        logging.basicConfig(filename=file2, level=logging.INFO, format='%(levelname)s-%(message)s - [%(module)s > %(filename)s> %(funcName)s]', datefmt=time.strftime("%d-%m-%Y,%H:%M:%S"))
        
        return logger


    def handle_sell_order(self, percentage_change, new_asset_price, asset_data, logger, counter):
        
        if percentage_change > self.increase_threeshold_for_update[asset_data['name']]:
            self.update_asset_reference_price(new_asset_price, asset_data, logger)
            counter['before_price_update'] = False
            return

        # 'significant' decrease just after 'buy' order -> update ref price + 'sell'
        if counter['before_price_update'] and percentage_change < self.sell_threeshold_before_price_update[asset_data['name']]:
            self.update_asset_reference_price(new_asset_price, asset_data, logger)
            logger.info(Functions().get_date() + 'Launch order "SELL" for ' + asset_data['name'] + ', percentage_change: ' + str(percentage_change))
            self.market_order(asset_data, "sell", logger)
            return

        # 'significant' decrease after last ref price update -> update ref price + 'sell'
        if not counter['before_price_update'] and (new_asset_price < (asset_data['price_reference'] - (asset_data['price_reference'] - asset_data['open_price']) / 3)) :
            self.update_asset_reference_price(new_asset_price, asset_data, logger)
            logger.info(Functions().get_date() + 'Launch order "SELL+" for ' + asset_data['name'] + ', percentage_change: ' + str(percentage_change))
            self.market_order(asset_data, "sell", logger)
            counter['before_price_update'] = True # reset this counter


    def handle_close_short_sell_order(self, percentage_change, new_asset_price, asset_data, logger, counter):
        
        # 'significant' increase just after 'short sell' order -> update ref price
        if percentage_change < self.decrease_threeshold_for_update[asset_data['name']]:
            self.update_asset_reference_price(new_asset_price, asset_data, logger)
            counter['before_price_update'] = False
            return
            
        # 'significant' increase just after short sell order-> update ref price + 'close short sell'
        if counter['before_price_update'] and percentage_change > self.close_short_sell_threeshold_before_price_update[asset_data['name']]:
            self.update_asset_reference_price(new_asset_price, asset_data, logger)
            logger.info(Functions().get_date() + 'Launch order "CLOSE SHORT SELL" for ' + asset_data['name'] + ', percentage_change: ' + str(percentage_change))
            self.market_order(asset_data, "close short sell", logger)
            return

        # 'significant' increase after last ref price update-> update ref price + 'close short sell'
        if not counter['before_price_update'] and (new_asset_price > (asset_data['open_price'] - (asset_data['open_price'] - asset_data['price_reference']) / 4)) :
            self.update_asset_reference_price(new_asset_price, asset_data, logger)
            logger.info(Functions().get_date() + 'Launch order "CLOSE SHORT SELL+" for ' + asset_data['name'] + ', percentage_change: ' + str(percentage_change))
            self.market_order(asset_data, "close short sell", logger)
            counter['before_price_update'] = True


    """ _summary_: delay when no open position yet (no buy or short sell 'in progress')
    """
    async def delay_when_no_open_position(self, pace):
        await asyncio.sleep(pace)
        
        
    """_summary_: delay when a position is open (buy or short sell)
    """        
    async def delay_when_position_is_open(self, pace):
        await asyncio.sleep(pace)