from typing import Any, Generic, TypeVar, Callable
from functools import total_ordering

T = TypeVar("T")

@total_ordering
class Coords:
    row: int
    col: int

    def __init__(self, row: int, col: int) -> None:
        self.row = row
        self.col = col

    def valid(self) -> bool:
        return self.row >= 0 and self.row < 20 and self.col >= 0 and self.col < 20

    def to_tuple(self) -> tuple[int, int]:
        return self.row, self.col

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Coords):
            raise NotImplemented
        return self.row == other.row and self.col == other.col

    def __lt__(self, other: Coords) -> bool:
        return (
            self.row < other.row
            if self.row != other.row else
            self.col < other.col
        )

    def __add__(self, other: Coords) -> Coords:
        return Coords(self.row + other.row, self.col + other.col)

    def __sub__(self, other: Coords) -> Coords:
        return Coords(self.row - other.row, self.col - other.col)

class Grid(Generic[T]):
    data: list[list[T]]

    def __getitem__(self, coords: Coords) -> T:
        return self.data[coords.row][coords.col]

    def __setitem__(self, coords: Coords, val: T) -> None:
        self.data[coords.row][coords.col] = val

    def __init__(self, vals: Callable[[Coords], T]) -> None:
        super().__init__()
        self.data = [[vals(Coords(row, col)) for col in range(20)] for row in range(20)]