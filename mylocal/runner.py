from sc2 import run_game, Race, Difficulty, maps
from sc2.player import Bot, Computer, Human
from Sc2botAI.BaseBot import BaseBot
from sc2 import bot_ai

run_game(
    maps.get("ReaperTraining1"),
    [Bot(Race.Terran, BaseBot(debug=True)), Computer(Race.Terran, Difficulty.VeryHard)],
    # [Human(Race.Terran), Computer(Race.Terran, Difficulty.VeryHard)],
    realtime=True,
)


