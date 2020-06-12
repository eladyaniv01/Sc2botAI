import enum


class UnitRole(enum.Enum):
    New = (0,)
    Idle = (1,)
    Defending = (
        2,
    )  # TODO   defending what ? some method to link Role with expansions or key locations
    Attacking = (
        3,
    )  # TODO   Attacking what ? some method to link Role with expansions or key locations
    Harassing = (
        4,
    )  # TODO   Harassing what ? some method to link Role with expansions or key locations
    Scouting = (
        4,
    )  # TODO   Scouting what ? some method to link Role with expansions or key locations

