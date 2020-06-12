import random

import sc2
from sc2.player import Bot, Computer
from BaseBot import BaseBot


class Dummy(BaseBot):
    pass

def main():
    map = random.choice(
        [
            "AbyssalReefLE",
            "AcropolisLE",
            "AutomatonLE",
            "BelShirVestigeLE",
            "CactusValleyLE",
            "CyberForestLE",
            "DiscoBloodbathLE",
            "EphemeronLE",
            "HonorgroundsLE",
            "KairosJunctionLE",
            "KingsCoveLE",
            "NewkirkPrecinctTE",
            "NewRepugnancyLE",
            "PaladinoTerminalLE",
            "PortAleksanderLE",
            "ProximaStationLE",
            "ThunderbirdLE",
            "TritonLE",
            "WintersGateLE",
            "WorldofSleepersLE",
            "YearZeroLE",
        ]
    )

    map = "AbyssalReefLE"
    sc2.run_game(
        sc2.maps.get(map),
        [Bot(sc2.Race.Terran, Dummy(debug=True)), Computer(sc2.Race.Zerg, sc2.Difficulty.VeryEasy), ],
        realtime=False,
        # sc2_version="4.10.1",
    )


if __name__ == "__main__":
    for i in range(1):
        print(f"i = {i}")
        main()