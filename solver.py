from dataclasses import dataclass, field
from typing import Optional
import random


@dataclass
class Placement:
    word: str
    clue: str
    row: int
    col: int
    direction: str  # 'across' or 'down'
    number: int = 0

    @property
    def length(self) -> int:
        return len(self.word)


class CrosswordSolver:
    GRID_SIZE = 17

    def __init__(self):
        self.grid: list[list[Optional[str]]] = []
        self.placements: list[Placement] = []

    def _reset(self):
        self.grid = [[None] * self.GRID_SIZE for _ in range(self.GRID_SIZE)]
        self.placements = []

    def generate(self, word_entries: list[dict], target: int = 10) -> Optional[dict]:
        entries = [e for e in word_entries if 4 <= len(e["word"]) <= 9]
        entries.sort(key=lambda e: -len(e["word"]))

        # Try multiple starting words if we don't get enough placements
        for start_idx in range(min(3, len(entries))):
            self._reset()
            ordered = entries[start_idx:] + entries[:start_idx]

            first = ordered[0]
            word = first["word"].upper()
            r = self.GRID_SIZE // 2
            c = (self.GRID_SIZE - len(word)) // 2
            self._place(word, r, c, "across")
            self.placements.append(Placement(word, first["clue"], r, c, "across"))

            remaining = [e for e in ordered[1:] if e["word"].upper() != word]

            # Greedy placement with multiple passes
            for _ in range(len(remaining) * 2):
                if len(self.placements) >= target:
                    break
                if not remaining:
                    break

                best = self._find_best_placement(remaining)
                if best:
                    entry, r2, c2, direction, _ = best
                    w = entry["word"].upper()
                    self._place(w, r2, c2, direction)
                    self.placements.append(Placement(w, entry["clue"], r2, c2, direction))
                    remaining = [e for e in remaining if e["word"].upper() != w]
                else:
                    # Rotate remaining to try different words
                    remaining = remaining[1:] + remaining[:1]

            if len(self.placements) >= 5:
                break

        if len(self.placements) < 4:
            return None

        cropped, offset_r, offset_c = self._crop()
        for p in self.placements:
            p.row -= offset_r
            p.col -= offset_c

        self._assign_numbers()
        return self._serialize(cropped)

    def _find_best_placement(self, remaining: list[dict]):
        best_score = -1
        best = None

        for entry in remaining[:12]:  # Check first 12 to keep it fast
            w = entry["word"].upper()
            positions = self._find_valid_positions(w)
            for r, c, direction, score in positions:
                if score > best_score:
                    best_score = score
                    best = (entry, r, c, direction, score)

        return best

    def _find_valid_positions(self, word: str) -> list[tuple]:
        positions = []
        for placed in self.placements:
            opp_dir = "down" if placed.direction == "across" else "across"
            for pi, pl in enumerate(placed.word):
                for wi, wl in enumerate(word):
                    if pl != wl:
                        continue
                    if placed.direction == "across":
                        r = placed.row - wi
                        c = placed.col + pi
                    else:
                        r = placed.row + pi
                        c = placed.col - wi
                    score = self._score_position(word, r, c, opp_dir)
                    if score >= 0:
                        positions.append((r, c, opp_dir, score))
        return positions

    def _score_position(self, word: str, row: int, col: int, direction: str) -> int:
        if not self._can_place(word, row, col, direction):
            return -1
        dr, dc = (0, 1) if direction == "across" else (1, 0)
        crossings = sum(
            1
            for i, letter in enumerate(word)
            if self.grid[row + dr * i][col + dc * i] == letter
        )
        return crossings

    def _can_place(self, word: str, row: int, col: int, direction: str) -> bool:
        dr, dc = (0, 1) if direction == "across" else (1, 0)
        pr, pc = dc, dr  # perpendicular deltas
        n = len(word)
        end_r = row + dr * (n - 1)
        end_c = col + dc * (n - 1)

        if not (0 <= row < self.GRID_SIZE and 0 <= col < self.GRID_SIZE):
            return False
        if not (0 <= end_r < self.GRID_SIZE and 0 <= end_c < self.GRID_SIZE):
            return False

        # Cell immediately before word must be empty
        br, bc = row - dr, col - dc
        if 0 <= br < self.GRID_SIZE and 0 <= bc < self.GRID_SIZE:
            if self.grid[br][bc] is not None:
                return False

        # Cell immediately after word must be empty
        ar, ac = end_r + dr, end_c + dc
        if 0 <= ar < self.GRID_SIZE and 0 <= ac < self.GRID_SIZE:
            if self.grid[ar][ac] is not None:
                return False

        has_crossing = False

        for i, letter in enumerate(word):
            r, c = row + dr * i, col + dc * i
            cell = self.grid[r][c]

            if cell is None:
                # Empty cell: no parallel word can be adjacent
                for sign in (-1, 1):
                    nr, nc = r + sign * pr, c + sign * pc
                    if 0 <= nr < self.GRID_SIZE and 0 <= nc < self.GRID_SIZE:
                        if self.grid[nr][nc] is not None:
                            return False
            elif cell == letter:
                # Occupied: verify there's a crossing (perpendicular) word here
                if not self._is_crossing_cell(r, c, direction):
                    return False
                has_crossing = True
            else:
                return False

        return has_crossing

    def _is_crossing_cell(self, r: int, c: int, direction: str) -> bool:
        perp = "down" if direction == "across" else "across"
        for p in self.placements:
            if p.direction != perp:
                continue
            dr, dc = (1, 0) if p.direction == "down" else (0, 1)
            for i in range(p.length):
                if p.row + dr * i == r and p.col + dc * i == c:
                    return True
        return False

    def _place(self, word: str, row: int, col: int, direction: str):
        dr, dc = (0, 1) if direction == "across" else (1, 0)
        for i, letter in enumerate(word):
            self.grid[row + dr * i][col + dc * i] = letter

    def _crop(self) -> tuple:
        min_r = min(p.row for p in self.placements)
        min_c = min(p.col for p in self.placements)
        max_r = max(
            p.row + (p.length - 1 if p.direction == "down" else 0)
            for p in self.placements
        )
        max_c = max(
            p.col + (p.length - 1 if p.direction == "across" else 0)
            for p in self.placements
        )

        # Add 1-cell border
        min_r = max(0, min_r - 1)
        min_c = max(0, min_c - 1)
        max_r = min(self.GRID_SIZE - 1, max_r + 1)
        max_c = min(self.GRID_SIZE - 1, max_c + 1)

        cropped = [
            [self.grid[r][c] for c in range(min_c, max_c + 1)]
            for r in range(min_r, max_r + 1)
        ]
        return cropped, min_r, min_c

    def _assign_numbers(self):
        # Collect all word-start positions and sort in reading order
        starts: dict[tuple, int] = {}
        positions = sorted(
            set((p.row, p.col) for p in self.placements),
            key=lambda pos: (pos[0], pos[1]),
        )
        for i, pos in enumerate(positions, start=1):
            starts[pos] = i

        for p in self.placements:
            p.number = starts[(p.row, p.col)]

    def _serialize(self, cropped_grid: list[list]) -> dict:
        rows = len(cropped_grid)
        cols = len(cropped_grid[0]) if rows > 0 else 0
        across = sorted(
            [p for p in self.placements if p.direction == "across"],
            key=lambda p: p.number,
        )
        down = sorted(
            [p for p in self.placements if p.direction == "down"],
            key=lambda p: p.number,
        )
        all_placements = across + down

        return {
            "rows": rows,
            "cols": cols,
            "grid": cropped_grid,
            "placements": [
                {
                    "word": p.word,
                    "clue": p.clue,
                    "row": p.row,
                    "col": p.col,
                    "direction": p.direction,
                    "number": p.number,
                    "length": p.length,
                }
                for p in all_placements
            ],
        }
