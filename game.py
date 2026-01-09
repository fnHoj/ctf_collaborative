from grid import Coords, Grid, dist
from random import randint
from typing import Any, Callable

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

class TeamObject:
    team: bool
    pos: Coords

    def __init__(self, team: bool, pos: Coords) -> None:
        self.team = team
        self.pos = pos

class Player(TeamObject):
    direction: int
    prison: bool
    flag: int

    def __init__(self, team: bool, pos: Coords, direction: int = 4, flag: int = -1, prison: bool = False) -> None:
        super().__init__(team, pos)
        self.direction = direction
        self.prison = prison
        self.flag = flag
    
    def safe(self) -> bool:
        return (self.pos.col >= 10) if self.team else (self.pos.col < 10)

class Flag(TeamObject):
    ground: bool
    destined: int

    def __init__(self, team: bool, pos: Coords, ground: bool = True, destined: int = 0) -> None:
        super().__init__(team, pos)
        self.ground = ground
        self.destined = destined

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
    flags: list[Flag]
    lprison_turns: int
    rprison_turns: int
    lprison_num: int
    rprison_num: int
    lscore: int
    rscore: int

    def __init__(self) -> None:
        super().__init__()
        self.flags = []
        self.players = [Player(False, Coords(i + 1, 1)) for i in range(3)] + [Player(True, Coords(i + 1, 18)) for i in range(3)]
        self.lprison_turns = 0
        self.rprison_turns = 0
        self.lprison_num = 0
        self.rprison_num = 0
        self.lscore = 0
        self.rscore = 0
        for _ in range(9):
            for _ in range(64):
                x = Coords(randint(1, 18), randint(1, 9))
                if self.barriers[x]:
                    continue
                self.flags.append(Flag(True, x))
                break
            for _ in range(64):
                x = Coords(randint(1, 18), randint(10, 18))
                if self.barriers[x]:
                    continue
                self.flags.append(Flag(False, x))
                break
    
    def turn(self) -> dict[str, Any]:
        res: list[dict[str, int | bool]] = []
        flags: list[dict[str, int]] = [
            {
                "prow": flag.pos.row,
                "pcol": flag.pos.col,
                "row": flag.pos.row,
                "col": flag.pos.col,
                "team": flag.team
            }
            for flag in self.flags
        ]
        if self.lprison_turns and any(self.lprison[player.pos] for player in self.players if not player.team and not player.prison):
            self.lprison_turns = 1
        if self.rprison_turns and any(self.rprison[player.pos] for player in self.players if player.team and not player.prison):
            self.rprison_turns = 1
        if self.lprison_turns:
            self.lprison_turns -= 1
            if not self.lprison_turns:
                self.lprison_num = 0
                for player in self.players:
                    if not player.team:
                        player.prison = False
        if self.rprison_turns:
            self.rprison_turns -= 1
            if not self.rprison_turns:
                self.rprison_num = 0
                for player in self.players:
                    if player.team:
                        player.prison = False
        for player in self.players:
            if player.prison or player.safe():
                continue
            for p1 in self.players:
                if p1.team == player.team or p1.prison or not p1.safe():
                    continue
                if dist(player.pos, p1.pos) <= 1:
                    player.prison = True
                    if ~player.flag:
                        self.flags[player.flag].pos = player.pos
                        self.flags[player.flag].ground = True
                        flags[player.flag]["prow"] = player.pos.row
                        flags[player.flag]["pcol"] = player.pos.col
                        flags[player.flag]["row"] = player.pos.row
                        flags[player.flag]["col"] = player.pos.col
                        player.flag = -1
                    if player.team:
                        player.pos = Coords(16 + self.rprison_num // 3, 16 + self.rprison_num % 3)
                        self.rprison_num += 1
                        if not self.rprison_turns:
                            self.rprison_turns = 64
                    else:
                        player.pos = Coords(16 + self.lprison_num // 3, 1 + self.lprison_num % 3)
                        self.lprison_num += 1
                        if not self.lprison_turns:
                            self.lprison_turns = 64
        for i, flag in enumerate(self.flags):
            if flag.destined:
                flag.destined -= 1
                if flag.destined:
                    continue
                flag.destined = 1
                for _ in range(64):
                    x = Coords(randint(1, 18), randint(1, 9) if flag.team else randint(10, 18))
                    if self.barriers[x]:
                        continue
                    flag.pos = x
                    flag.destined = 0
                    flags[i]["row"] = flag.pos.row
                    flags[i]["col"] = flag.pos.col
                    break
        for player in self.players:
            p: dict[str, int | bool] = {"team": player.team, "row": player.pos.row, "col": player.pos.col}
            target = player.pos
            if ~player.flag:
                if self.rtarget[player.pos] if player.team else self.ltarget[player.pos]:
                    if player.team:
                        self.rscore += 1
                    else:
                        self.lscore += 1
                    self.flags[player.flag].pos = player.pos
                    self.flags[player.flag].ground = True
                    self.flags[player.flag].destined = 8
                    flags[player.flag]["prow"] = player.pos.row
                    flags[player.flag]["pcol"] = player.pos.col
                    flags[player.flag]["row"] = player.pos.row
                    flags[player.flag]["col"] = player.pos.col
                    player.flag = -1
            else:
                for i, flag in enumerate(self.flags):
                    if not flag.destined and flag.team == player.team and flag.pos == player.pos:
                        flag.ground = False
                        player.flag = i
                        break
            if not player.prison:
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
            p["direction"] = 4 if player.prison else player.direction
            p["flag"] = bool(~player.flag)
            p["prison"] = player.prison
            res.append(p)
        return {
            "players": res,
            "flags": [flag for i, flag in enumerate(flags) if self.flags[i].ground],
            "lscore": self.lscore,
            "rscore": self.rscore
        }
