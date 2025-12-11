import configparser
import redis

config = configparser.ConfigParser()
config.read('conf.ini')
redis = redis.Redis(host=config['REDIS']['host'], port=config['REDIS']['port'], db=config['REDIS']['db'])

if redis.flushdb():
    print('redis cleaned !')
else:
    raise Exception('flush redis failed !')