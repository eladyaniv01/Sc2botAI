import enum
# inspired by sharpy - rapid bot development framework: https://github.com/DrInfy/sharpy-sc2


class BlockerType(enum.Enum):
    Building1x1 = 1,
    Building2x2 = 2,
    Building3x3 = 3,
    Building4x4 = 4,
    Building5x5 = 5,
    Building6x6 = 6,
    Minerals = 12,