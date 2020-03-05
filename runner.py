from sc2 import run_game, Race, Difficulty, maps
from sc2.player import Bot, Computer
from Sc2botAI.BaseBot import BaseBot

run_game(
    maps.get("AutomatonLE"),
    [Bot(Race.Terran, BaseBot(debug=True)), Computer(Race.Protoss, Difficulty.Easy)],
    realtime=True,
)
