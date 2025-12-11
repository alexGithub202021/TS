import configparser
import redis

config = configparser.ConfigParser()
config.read('conf.ini')
redis = redis.Redis(host=config['REDIS']['host'], port=config['REDIS']['port'], db=config['REDIS']['db'])

print(' *** Redis collections: ')

if 0 == len(redis.keys()):
    print(' empty !')
else:
    for k in redis.keys():
        print(k.decode())