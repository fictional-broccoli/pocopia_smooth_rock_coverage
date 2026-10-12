import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from main import NoSolutionError, build_grid, main, optimize, parse_pattern


class PatternTests(unittest.TestCase):
    def test_parse_bracket_notation(self):
        self.assertEqual(
            parse_pattern("[s][d][s][d]"),
            "sdsd",
        )

    def test_builds_ten_rows(self):
        grid = build_grid("[s][d]")
        self.assertEqual(len(grid), 10)
        self.assertTrue(all(row == "sd" for row in grid))

    def test_builds_requested_number_of_rows(self):
        self.assertEqual(build_grid("[d]", rows=3), ["d", "d", "d"])

    def test_invalid_pattern(self):
        with self.assertRaises(ValueError):
            parse_pattern("sxd")

    def test_empty_pattern(self):
        with self.assertRaises(ValueError):
            parse_pattern("[]")


class OptimizationTests(unittest.TestCase):
    def test_no_targets(self):
        result = optimize(["sss"], max_stones=3)
        self.assertEqual(result.covered_count, 0)
        self.assertEqual(result.stones, ())
        self.assertEqual(result.overlap_count, 0)

    def test_zero_stones(self):
        with self.assertRaises(NoSolutionError):
            optimize(["d"], max_stones=0, radius=1)

    def test_stones_are_placed_on_targets(self):
        result = optimize(["d"], max_stones=1, radius=0)
        self.assertEqual(result.stones, ((0, 0),))
        self.assertEqual(result.covered_count, 1)
        self.assertEqual(result.uncovered_count, 0)

    def test_full_coverage_maximizes_overlap(self):
        result = optimize(["ddd"], max_stones=2, radius=1)
        self.assertEqual(result.covered_count, 3)
        self.assertEqual(result.uncovered_count, 0)
        self.assertLessEqual(len(result.stones), 2)
        self.assertEqual(result.overlap_count, 5)
        self.assertEqual(result.covered, {(0, 0), (0, 1), (0, 2)})
        self.assertTrue(all("ddd"[column] == "d" for _, column in result.stones))

    def test_infeasible_limit_does_not_return_partial_solution(self):
        with self.assertRaises(NoSolutionError):
            optimize(["ddddd"], max_stones=1, radius=1)

    def test_manhattan_radius_excludes_diagonal_cell(self):
        with self.assertRaises(NoSolutionError):
            optimize(["dd", "dd"], max_stones=1, radius=1)

    def test_negative_stone_limit(self):
        with self.assertRaises(ValueError):
            optimize(["sds"], max_stones=-1)

    def test_non_rectangular_grid(self):
        with self.assertRaises(ValueError):
            optimize(["sd", "s"], max_stones=1)

    def test_invalid_cell(self):
        with self.assertRaises(ValueError):
            optimize(["dx"], max_stones=1)

    def test_non_integer_limit_is_reported(self):
        output = StringIO()
        with (
            patch("builtins.input", side_effect=("[d]", "", "many")),
            redirect_stdout(output),
        ):
            main()
        self.assertIn("岩の上限は整数で入力してください", output.getvalue())

    def test_non_integer_row_count_is_reported(self):
        output = StringIO()
        with (
            patch("builtins.input", side_effect=("[d]", "many", "1")),
            redirect_stdout(output),
        ):
            main()
        self.assertIn("行数は整数で入力してください", output.getvalue())

    def test_main_uses_requested_number_of_rows(self):
        output = StringIO()
        with (
            patch("builtins.input", side_effect=("[d]", "2", "1")),
            redirect_stdout(output),
        ):
            main()
        self.assertIn("乾燥対象: 2", output.getvalue())

    def test_main_reports_infeasible_limit_without_partial_result(self):
        output = StringIO()
        with (
            patch("builtins.input", side_effect=("[d][d]", "", "1")),
            redirect_stdout(output),
        ):
            main()
        self.assertIn("すべての乾燥対象をカバーできません", output.getvalue())
        self.assertNotIn("カバーしたマス:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
