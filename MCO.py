from api import API
from logMonitor import logMonitor
from config import Config
import time

# Default configuration
defaultConfig = {
    "ownUsers": [
        "cocodef9"
    ],
    "token": "token",
    "logFolder": "C:\\Users\\sjoer\\Appdata\\Roaming\\Minecraft 1.8.9\\logs\\latest.log"
}

# Load configuration file (if empty, loads defaultConfig)
config = Config('./config/config.json', defaultConfig)
players = Config('./config/players.json', {})

# Save the configuration file
config.save()

# Create a configuration file logger
logger = logMonitor(config.get("logFolder"), True)

# Create an API object
api = API(players.config)

# Reset log
open('./config/log.txt', 'w').close()

def start():
    for user in config.get("ownUsers"):
        print("User: {} has UUID: {}".format(user, api.minecraft(user)))
    while(True):
        logger.tick()
        if (logger.hasQueue):
            for element in logger.getPlayers():
                uuid = api.minecraft(element)
                print("Player {} has UUID {}".format(element, uuid))
                players.set(element, uuid)
                players.set(uuid, element)
        time.sleep(0.1)


if (__name__ == "__main__"):
    start()