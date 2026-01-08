from grid import Coords, Grid, Callable
from random import randint

class Obstacle:
    pos: Coords
    tall: bool

    def __init__(self, pos: Coords, tall: bool = False) -> None:
        self.pos = pos
        self.tall = tall

def grid_range(r0: int, c0: int, r1: int, c1: int, invert: bool = False) -> Callable[[Coords], bool]:
    if invert:
        return lambda x: x.row < r0 or x.row >= r1 or x.col < c0 or x.col >= c1
    return lambda x: x.row >= r0 and x.row < r1 and x.col >= c0 and x.col < c1

class Player:
    team: bool
    pos: Coords
    direction: int
    prison: bool
    def __init__(self, team: bool, pos: Coords, direction: int = 0, prison: bool = False) -> None:
        self.team = team
        self.pos = pos
        self.direction = direction
        self.prison = prison

class Board:
    barriers: Grid[bool]
    obstacles: list[Obstacle]
    ltarget: Grid[bool]
    rtarget: Grid[bool]
    lprison: Grid[bool]
    rprison: Grid[bool]
    lstart: Grid[bool]
    rstart: Grid[bool]

    def is_occupied(self, x: Coords) -> bool:
        return self.barriers[x] or self.ltarget[x] or self.rtarget[x] or self.lprison[x] or self.rprison[x] or self.lstart[x] or self.rstart[x]

    def __init__(self) -> None:
        self.barriers = Grid(grid_range(1, 1, 19, 19, True))
        self.ltarget = Grid(grid_range(9, 1, 12, 4))
        self.rtarget = Grid(grid_range(9, 16, 12, 19))
        self.lprison = Grid(grid_range(16, 1, 19, 4))
        self.rprison = Grid(grid_range(16, 16, 19, 19))
        self.lstart = Grid(grid_range(1, 1, 4, 2))
        self.rstart = Grid(grid_range(1, 18, 4, 19))
        self.obstacles = []
        for _ in range(4):
            for _ in range(0x10):
                x = Coords(randint(1, 17), randint(1, 18))
                x1 = x + Coords(1, 0)
                if self.is_occupied(x) or self.is_occupied(x1):
                    continue
                self.obstacles.append(Obstacle(x, True))
                self.barriers[x] = True
                self.barriers[x1] = True
                break
        for _ in range(8):
            for _ in range(0x10):
                x = Coords(randint(1, 17), randint(1, 18))
                if self.is_occupied(x):
                    continue
                self.obstacles.append(Obstacle(x))
                self.barriers[x] = True
                break

class Game(Board):
    players: list[Player]
    lprison_turns: int
    rprison_turns: int
    lscore: int
    rscore: int

    def __init__(self) -> None:
        super().__init__()
        self.players = [Player(False, Coords(i + 1, 1)) for i in range(3)] + [Player(True, Coords(i + 1, 18)) for i in range(3)]
        self.lprison_turns = 0
        self.rprison_turns = 0
        self.lscore = 0
        self.rscore = 0
    
    def turn(self) -> list[dict[str, int | bool]]:
        res: list[dict[str, int | bool]] = []
        for player in self.players:
            p: dict[str, int | bool] = {"team": player.team, "row": player.pos.row, "col": player.pos.col}
            target = player.pos
            if player.direction == 0:
                target += Coords(1, 0)
            elif player.direction == 1:
                target += Coords(-1, 0)
            elif player.direction == 2:
                target += Coords(0, 1)
            elif player.direction == 3:
                target += Coords(0, -1)
            if not target.valid() or self.barriers[target]:
                player.direction = 4
                target = player.pos
            player.pos = target
            p["direction"] = player.direction
            res.append(p)
        return res
