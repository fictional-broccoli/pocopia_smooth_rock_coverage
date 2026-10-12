"""Optimize placement of さらさら岩 on a repeated 2D pattern."""

from __future__ import annotations

import re
from dataclasses import dataclass

ROWS = 10
DRYING_RADIUS = 5


@dataclass(frozen=True)
class Result:
    stones: tuple[tuple[int, int], ...]
    covered: frozenset[tuple[int, int]]
    total_targets: int
    overlap_count: int

    @property
    def covered_count(self) -> int:
        return len(self.covered)

    @property
    def uncovered_count(self) -> int:
        return self.total_targets - self.covered_count


def parse_pattern(pattern: str) -> str:
    """Accept strings such as 'sdsd' or '[s][d][s][d]'."""
    normalized = re.sub(r"[\[\]\s]", "", pattern).lower()

    if not normalized:
        raise ValueError("パターンが空です。")

    invalid = set(normalized) - {"s", "d"}
    if invalid:
        raise ValueError(f"使用できない文字があります: {sorted(invalid)}")

    return normalized


def build_grid(pattern: str, rows: int = ROWS) -> list[str]:
    """Repeat the same 1D pattern for the specified number of rows."""
    pattern = parse_pattern(pattern)

    if rows < 1:
        raise ValueError("行数は1以上にしてください。")

    return [pattern for _ in range(rows)]


def optimize(
    grid: list[str],
    max_stones: int,
    radius: int = DRYING_RADIUS,
) -> Result:
    """Find a full-coverage placement maximizing total d-cell coverage count.

    Assumptions:
    - Stones can only be placed on d-cells.
    - A d-cell is covered if Manhattan distance <= radius.
    - At most max_stones stones may be placed.
    - Every d-cell must be covered; partial solutions are not returned.
    """
    if max_stones < 0:
        raise ValueError("岩の上限は0以上にしてください。")
    if radius < 0:
        raise ValueError("効果半径は0以上にしてください。")
    if not grid or not grid[0]:
        raise ValueError("地形が空です。")

    width = len(grid[0])
    if any(len(row) != width for row in grid):
        raise ValueError("地形の各行は同じ幅にしてください。")
    if any(set(row) - {"s", "d"} for row in grid):
        raise ValueError("地形には s と d だけを使用してください。")

    targets = [
        (r, c)
        for r, row in enumerate(grid)
        for c, cell in enumerate(row)
        if cell == "d"
    ]
    target_index = {pos: i for i, pos in enumerate(targets)}

    if not targets:
        return Result((), frozenset(), 0, 0)

    # Each candidate is represented by the bitmask of d-cells it covers.
    candidates: list[tuple[tuple[int, int], int]] = []

    for r, row in enumerate(grid):
        for c, cell in enumerate(row):
            if cell != "d":
                continue

            mask = 0
            for tr, tc in targets:
                if abs(r - tr) + abs(c - tc) <= radius:
                    mask |= 1 << target_index[(tr, tc)]

            if mask:
                candidates.append(((r, c), mask))

    candidates.sort(
        key=lambda item: item[1].bit_count(),
        reverse=True,
    )

    n = len(candidates)
    limit = min(max_stones, n)

    # Union of all candidate coverage masks from each index onward.
    suffix_union = [0] * (n + 1)
    for i in range(n - 1, -1, -1):
        suffix_union[i] = suffix_union[i + 1] | candidates[i][1]

    full_mask = (1 << len(targets)) - 1
    best_overlap_count = -1
    best_mask = 0
    best_indices: tuple[int, ...] = ()

    def search(
        start: int,
        remaining: int,
        covered: int,
        overlap_count: int,
        chosen: tuple[int, ...],
    ) -> None:
        nonlocal best_overlap_count, best_mask, best_indices

        if covered == full_mask and overlap_count > best_overlap_count:
            best_overlap_count = overlap_count
            best_mask = covered
            best_indices = chosen

        if remaining == 0 or start == n:
            return

        # No selection from the remaining candidates can complete coverage.
        if covered | suffix_union[start] != full_mask:
            return

        # Each remaining stone adds at most its full mask size to the score.
        upper_bound = overlap_count + sum(
            mask.bit_count() for _, mask in candidates[start : start + remaining]
        )
        if upper_bound <= best_overlap_count:
            return

        # Branch 1: place a stone at this candidate.
        _, mask = candidates[start]
        search(
            start + 1,
            remaining - 1,
            covered | mask,
            overlap_count + mask.bit_count(),
            chosen + (start,),
        )

        # Branch 2: do not place a stone here.
        search(start + 1, remaining, covered, overlap_count, chosen)

    search(0, limit, 0, 0, ())

    if best_overlap_count < 0:
        raise NoSolutionError(
            "指定された岩の上限以内では、すべての乾燥対象をカバーできません。"
        )

    covered_cells = frozenset(
        targets[i] for i in range(len(targets)) if best_mask & (1 << i)
    )
    stones = tuple(candidates[i][0] for i in best_indices)

    return Result(stones, covered_cells, len(targets), best_overlap_count)


class NoSolutionError(Exception):
    """Raised when the stone limit cannot cover every target cell."""


def print_result(grid: list[str], result: Result) -> None:
    """Print the placement and coverage using a simple text grid."""
    stone_set = set(result.stones)

    for r, row in enumerate(grid):
        cells = []
        for c, cell in enumerate(row):
            if (r, c) in stone_set:
                cells.append("[R]")
            elif cell == "d":
                cells.append("[D]" if (r, c) in result.covered else "[d]")
            else:
                cells.append("[s]")
        print("".join(cells))

    print()
    print(f"岩の使用数: {len(result.stones)}")
    print(f"乾燥対象: {result.total_targets}")
    print(f"カバーしたマス: {result.covered_count}")
    print(f"未カバーのマス: {result.uncovered_count}")
    print(f"効果範囲の重複回数（被覆数合計）: {result.overlap_count}")
    print("※重複回数は乾燥判定頻度の代理指標で、実際の乾燥時間ではありません。")
    print("岩の座標（行, 列・0始まり）:", result.stones)


def main() -> None:
    try:
        pattern = input("配置パターン / Pattern (e.g. [s][d][s][d][s]): ")
        rows_text = input(f"繰り返し行数 / Repeated rows (default: {ROWS}): ").strip()
        try:
            rows = ROWS if not rows_text else int(rows_text)
        except ValueError as error:
            raise ValueError("行数は整数で入力してください。") from error

        max_stones_text = input("さらさら岩の上限 / Smooth Rock limit: ")
        try:
            max_stones = int(max_stones_text)
        except ValueError as error:
            raise ValueError("岩の上限は整数で入力してください。") from error

        grid = build_grid(pattern, rows)
        result = optimize(grid, max_stones)
        print_result(grid, result)
    except (ValueError, NoSolutionError) as error:
        print(f"エラー: {error}")


if __name__ == "__main__":
    main()
