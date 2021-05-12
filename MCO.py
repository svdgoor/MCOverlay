from PlayerQueue import PlayerQueue
from Enums import GameOrigin as GO, CommandOrigin as CO, SystemEvents as SE, SystemStatus as SS
from API import API
from LogMonitor import LogMonitor
from CommandSender import CommandSender
from Config import Config
import time

defaultConfig = {
    "ownUsername": "cocodef9",
    "token": "206baa63-dcd2-47f3-b197-b43de4e3301f",
    "logFolder": "C:\\Users\\sjoer\\Appdata\\Roaming\\Minecraft 1.8.9\\logs\\latest.log",
    "downloadStatsOfPlayersIn": {
        GO.mainChat: True,
        GO.mainLobby: True,
        GO.gameChat: True,
        GO.gameLobby: True
    },
    "autoCommands": {
        "autoWho": True,
        "autoInvite": True,
        "autoLeave": True,
        "autoPWarp": True,
        "autoPList": True,
        "autoLeavePartyDC": True
    },
    "autoInviteStatBypass": [
        "dungeoneer1",
        "Prems",
        "gussie842",
        "cocodef9",
        "ReadyPlayerFour",
        "dungeoneer2"
    ],
    "leavePartyMemberMissing": True,
    "enableStatistics-Do-Not-Disable!": True
}
defaultController = {
    "stop": False,
    "getAPI": False
}

class MCO:

    status = SS.none
    config = None
    controller = None
    logger = None
    autoInviteToggle = True
    commandSender = None

    def __init__(self):
        
        self.status = SS.startup
        self.file(SE.notify, "Initalizing MCO...")

        # Configuration
        self.file(SE.notify, "Loading configuration")
        self.config = Config('./config/config.json', defaultConfig)

        # Controller
        self.file(SE.notify, "Loading controller")
        self.controller = Config('./config/controller.json', defaultController)

        # LogMonitor
        self.file(SE.notify, "Loading log monitor")
        self.logger = LogMonitor(
            self.config.get("logFolder"), 
            self.config.get("ownUsername"), 
            False
        )
        self.status = SS.oldLogs
        self.file(SE.notify, "Loading old logs (if any)")
        self.logger.tick(True)
        self.logger.tick(True)
        self.logger.resetExposed()
        self.status = SS.startup
        self.file(SE.notify, "Loaded old logs")

        # API
        self.file(SE.notify, "Loading API")
        self.api = API(self.config.get("token"), True)
        self.file(SE.api, self.api.hypixelStats())
        self.file(SE.api, self.api.minecraftStats())

        # CommandSender
        self.file(SE.notify, "Loading Command Sender")
        self.commandSender = CommandSender()

        # Update status
        self.status = SS.waiting
        self.file(SE.notify, "Finished initializing")

    def start(self):

        try:

            # Update status
            self.status = SS.running

            # Run PList and who commands
            time.sleep(1)
            self.commandSender.plist(CO.startup)
            time.sleep(0.25)
            self.commandSender.who(CO.startup)
            
            cycle = 0

            # Main loop
            self.file(SE.notify, "Starting main loop")
            while True:

                # Update cycle number (1 per second)
                cycle += 0.1

                if cycle % 60 == 0:
                    self.file(SE.api, self.api.hypixelStats())
                    self.file(SE.api, self.api.minecraftStats())

                # Update logger
                self.logger.tick()

                # See if there are config changes
                self.config.hotload()

                # Check for logger tasks
                self.loggerTasks()

                # Update player definitions
                self.statisticsTask()

                # Check controller
                if self.controllerTask(): break

                # Wait a short while before refreshing
                # Note: This can be decreased to increase responsiveness,
                #       but it may break certain elements of the program.
                # Use at your own risk
                time.sleep(0.1)

        except Exception as e:
            self.commandSender.available = False
            self.file(SE.error, "An uncaught exception has been raised in the main loop: {}".format(e))
            self.file(SE.error, "Disabling all command outputs of the program to prevent potential damage")


        # Shutdown
        self.status = SS.shutdown
        self.file(SE.notify, "Closing MCO")
        exit()
        
    def loggerTasks(self):
        # Check for token update
        if self.logger.newToken != None:
            self.api.token = self.logger.newToken
            self.config.set("token", self.logger.newToken)
            self.config.save()
            self.logger.newToken = None

        # Check for autowho
        if self.logger.autoWho:
            self.logger.autoWho = False
            if self.config.get("autoCommands")["autoWho"]: self.commandSender.who(CO.autowho)

        # Check for autoplist
        if self.logger.autoPartyList:
            self.logger.autoPartyList = False
            if self.config.get("autoCommands")["autoPList"]: self.commandSender.plist(CO.autoplist)

        # Check for logger party member missing tier 2
        if self.logger.partyMemberMissingTwo:
            self.logger.partyMemberMissingTwo = False
            if self.config.get("leavePartyMemberMissing"): self.commandSender.pleave(CO.partymissing)

        # Check for autoleave
        if self.logger.autoLeave:
            self.logger.autoLeave = False
            time.sleep(2)
            if self.config.get("autoCommands")["autoLeave"]: 
                self.commandSender.leave(CO.autoleave)
                if self.logger.party != None and len(self.logger.party) > 1 and self.config.get("autoCommands")["autoPWarp"]:
                    time.sleep(0.5)
                    self.commandSender.pwarp(CO.autoleave)
            elif self.config.get("autoCommands")["autoPWarp"]:
                self.commandSender.pwarp(CO.autoleave)

        # Check for party member DC
        if self.logger.autoLeavePartyLeave:
            self.logger.autoLeavePartyLeave = False
            if self.config.get("autoCommands")["autoLeavePartyDC"]:
                self.commandSender.leave(CO.partyleft)
                time.sleep(0.25)
                self.commandSender.pwarp(CO.partyleft)

        # Check for failed autowho's by others
        if len(self.logger.failedWho) > 0:
            for name in self.logger.failedWho:
                # TODO: Add to statistics flags
                print("Failed /who by: " + name)
            self.logger.failedWho = []
            
        # Check for stats reset (/who)
        if self.logger.resetStats:
            self.logger.resetStats = False
            q = PlayerQueue()
            for player in self.logger.party:
                q.add(player, origin=GO.party)
            q.add(self.config.get("ownUsername"))

        # Check for autoinvite
        if len(self.logger.autoInvite) > 0 and self.autoInviteToggle:
            inv = self.logger.autoInvite.copy()
            self.logger.autoInvite = []
            if self.config.get("autoCommands")["autoInvite"]:
                for player in inv:
                    if player in self.config.get("autoInviteStatBypass"):
                        self.commandSender.type("/p " + player, CO.autoinvite)
                    elif True: #TODO: Add auto statistics check and invite
                        self.commandSender.type("/p " + player, CO.autoinvite)

    def controllerTask(self):
        self.controller.hotload()
        if self.controller.get("stop"):
            self.controller.set("stop", False)
            self.controller.save()
            return True
        if self.controller.get("getAPI"):
            self.controller.set("getAPI", False)
            self.controller.save()
            self.file(SE.api, self.api.hypixelStats())
            self.file(SE.api, self.api.minecraftStats())
            return False

    def statisticsTask(self):
        if self.config.get("enableStatistics-Do-Not-Disable!"):
            pd = self.config.get("downloadStatsOfPlayersIn")
            q = {}
            queue = self.logger.queue.get()
            for player in queue.keys():
                origin = queue[player]["origin"]
                if ((origin == GO.mainChat and pd[GO.mainChat]) or
                    (origin == GO.mainLobby and pd[GO.mainLobby]) or
                    (origin == GO.gameChat and pd[GO.gameChat]) or
                    (origin == GO.gameLobby and pd[GO.gameLobby]) or
                    (origin == GO.party)):
                    q[player] = queue[player]
            self.api.fetch(q)

    def file(self, type: str, line: str):
        """Prints a line to console in the proper format
        
        Args:
            type (str): The type of event
            line (str): The line to print
        """
        line = "[SYSTEM] {} | {}: {}".format(
            self.status + (SS.maxStatusLength - len(self.status)) * " ",
            type + (SE.maxEventLength - len(type)) * " ",
            line
        )
        line = line if len(line) < 150 else line[:150].strip() + " (...)"
        print(line)


if __name__ == '__main__':
    MCO().start()