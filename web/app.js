"use strict";

const DRYING_RADIUS = 5;

const form = document.querySelector("#optimizer-form");
const patternInput = document.querySelector("#pattern-input");
const rowsInput = document.querySelector("#rows-input");
const stoneLimitInput = document.querySelector("#stone-limit-input");
const efficiencyInput = document.querySelector("#efficiency-input");
const optimizationSummary = document.querySelector("#optimization-summary");
const errorMessage = document.querySelector("#error-message");
const emptyState = document.querySelector("#empty-state");
const resultPanel = document.querySelector("#result-panel");
const resultBadge = document.querySelector("#result-badge");
const gridOutput = document.querySelector("#grid-output");

function parsePattern(value) {
    const pattern = value.replace(/[\[\]\s]/g, "").toLowerCase();
    if (!pattern) {
        throw new Error("パターンを入力してください。 / Enter a pattern.");
    }
    if (/[^sd]/.test(pattern)) {
        throw new Error("パターンには s と d だけを使用してください。 / Use only s and d.");
    }
    return pattern;
}

function parseInteger(value, label, minimum) {
    if (String(value).trim() === "") {
        throw new Error(`${label}を入力してください。 / Enter ${label}.`);
    }
    const parsed = Number(value);
    if (!Number.isSafeInteger(parsed) || parsed < minimum) {
        throw new Error(`${label}は${minimum}以上の整数で入力してください。`);
    }
    return parsed;
}

function buildGrid(pattern, rows) {
    const normalized = parsePattern(pattern);
    const rowCount = parseInteger(String(rows), "行数 / Row count", 1);
    return Array.from({ length: rowCount }, () => normalized);
}

function bitCount(mask) {
    let count = 0;
    while (mask !== 0n) {
        mask &= mask - 1n;
        count += 1;
    }
    return count;
}

function optimize(grid, maxStones, maximizeEfficiency = false) {
    const stoneLimit = parseInteger(String(maxStones), "岩の上限 / Stone limit", 0);
    if (!grid.length || !grid[0].length) {
        throw new Error("地形が空です。 / The grid is empty.");
    }

    const width = grid[0].length;
    if (grid.some((row) => row.length !== width)) {
        throw new Error("地形の各行は同じ幅にしてください。 / Grid rows must have equal width.");
    }

    const targets = [];
    for (let row = 0; row < grid.length; row += 1) {
        for (let column = 0; column < width; column += 1) {
            const cell = grid[row][column];
            if (cell !== "s" && cell !== "d") {
                throw new Error("地形には s と d だけを使用してください。 / Use only s and d in the grid.");
            }
            if (cell === "d") {
                targets.push({ row, column });
            }
        }
    }

    if (targets.length === 0) {
        return { stones: [], targets, overlapCount: 0, efficiency: null };
    }

    const candidates = [];
    for (const target of targets) {
        let mask = 0n;
        for (let index = 0; index < targets.length; index += 1) {
            const other = targets[index];
            if (
                Math.abs(target.row - other.row) + Math.abs(target.column - other.column)
                <= DRYING_RADIUS
            ) {
                mask |= 1n << BigInt(index);
            }
        }
        candidates.push({
            row: target.row,
            column: target.column,
            mask,
            coverageCount: bitCount(mask),
        });
    }

    candidates.sort((left, right) => right.coverageCount - left.coverageCount);

    const candidateCount = candidates.length;
    const limit = Math.min(stoneLimit, candidateCount);
    const suffixUnion = Array(candidateCount + 1).fill(0n);
    for (let index = candidateCount - 1; index >= 0; index -= 1) {
        suffixUnion[index] = suffixUnion[index + 1] | candidates[index].mask;
    }

    const fullMask = (1n << BigInt(targets.length)) - 1n;
    let bestOverlapCount = -1;
    let bestStoneCount = -1;
    let bestIndices = [];

    function search(start, remaining, covered, overlapCount, chosen) {
        if (covered === fullMask) {
            let isBetter = overlapCount > bestOverlapCount;
            if (maximizeEfficiency && bestOverlapCount >= 0) {
                const candidateRatio = overlapCount * bestStoneCount;
                const bestRatio = bestOverlapCount * chosen.length;
                isBetter = candidateRatio > bestRatio
                    || (candidateRatio === bestRatio
                        && (overlapCount > bestOverlapCount
                            || (overlapCount === bestOverlapCount && chosen.length < bestStoneCount)));
            }
            if (isBetter) {
                bestOverlapCount = overlapCount;
                bestStoneCount = chosen.length;
                bestIndices = chosen;
            }
        }

        if (remaining === 0 || start === candidateCount) {
            return;
        }
        if ((covered | suffixUnion[start]) !== fullMask) {
            return;
        }

        if (maximizeEfficiency) {
            if (bestOverlapCount >= 0) {
                let upperNumerator = overlapCount;
                let upperDenominator = chosen.length;
                const bestRemainingSingle = candidates[start].coverageCount;
                if (
                    upperDenominator === 0
                    || bestRemainingSingle * upperDenominator > upperNumerator
                ) {
                    upperNumerator = bestRemainingSingle;
                    upperDenominator = 1;
                }
                if (upperNumerator * bestStoneCount < bestOverlapCount * upperDenominator) {
                    return;
                }
            }
        } else {
            let upperBound = overlapCount;
            const end = Math.min(candidateCount, start + remaining);
            for (let index = start; index < end; index += 1) {
                upperBound += candidates[index].coverageCount;
            }
            if (upperBound <= bestOverlapCount) {
                return;
            }
        }

        const candidate = candidates[start];
        search(
            start + 1,
            remaining - 1,
            covered | candidate.mask,
            overlapCount + candidate.coverageCount,
            [...chosen, start],
        );
        search(start + 1, remaining, covered, overlapCount, chosen);
    }

    search(0, limit, 0n, 0, []);

    if (bestOverlapCount < 0) {
        throw new Error(
            "指定された岩の上限以内では、すべての乾燥対象をカバーできません。\n"
            + "All drying targets cannot be covered within the stone limit.",
        );
    }

    const stones = bestIndices.map((index) => ({
        row: candidates[index].row,
        column: candidates[index].column,
    }));
    return {
        stones,
        targets,
        overlapCount: bestOverlapCount,
        efficiency: bestOverlapCount / stones.length,
    };
}

function renderGrid(grid, solution) {
    const rockPositions = new Set(
        solution.stones.map(({ row, column }) => `${row}:${column}`),
    );
    const targetPositions = new Set(
        solution.targets.map(({ row, column }) => `${row}:${column}`),
    );
    gridOutput.replaceChildren();

    for (let row = 0; row < grid.length; row += 1) {
        const rowElement = document.createElement("div");
        rowElement.className = "grid-row";
        rowElement.setAttribute("role", "row");
        rowElement.style.setProperty("--column-count", grid[row].length);

        const rowLabel = document.createElement("span");
        rowLabel.className = "row-label";
        rowLabel.setAttribute("role", "rowheader");
        rowLabel.textContent = String(row);
        rowElement.append(rowLabel);

        for (let column = 0; column < grid[row].length; column += 1) {
            const position = `${row}:${column}`;
            const cell = document.createElement("span");
            cell.className = "grid-cell";
            cell.setAttribute("role", "gridcell");

            if (rockPositions.has(position)) {
                cell.classList.add("cell-rock");
                cell.textContent = "R";
                cell.title = `岩の位置 / Rock: (${row}, ${column})`;
            } else if (grid[row][column] === "d") {
                cell.classList.add("cell-covered");
                cell.textContent = "D";
                cell.title = targetPositions.has(position)
                    ? `カバー済み / Covered: (${row}, ${column})`
                    : `未カバー / Uncovered: (${row}, ${column})`;
            } else {
                cell.classList.add("cell-s");
                cell.textContent = "S";
                cell.title = `乾燥不要 / No drying needed: (${row}, ${column})`;
            }
            rowElement.append(cell);
        }
        gridOutput.append(rowElement);
    }
}

function showSolution(grid, solution) {
    const targetCount = solution.targets.length;
    document.querySelector("#stone-count").textContent = String(solution.stones.length);
    document.querySelector("#target-count").textContent = `${targetCount} / ${targetCount}`;
    document.querySelector("#overlap-count").textContent = String(solution.overlapCount);
    document.querySelector("#efficiency-score").textContent = solution.efficiency === null
        ? "—"
        : solution.efficiency.toFixed(2);

    const coordinates = solution.stones.map(({ row, column }) => `(${row}, ${column})`);
    document.querySelector("#coordinate-list").textContent = coordinates.length
        ? coordinates.join(" · ")
        : "なし / None";

    renderGrid(grid, solution);
    errorMessage.hidden = true;
    emptyState.hidden = true;
    resultPanel.hidden = false;
    resultBadge.hidden = false;
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    errorMessage.hidden = true;
    resultPanel.hidden = true;
    resultBadge.hidden = true;

    try {
        const pattern = parsePattern(patternInput.value);
        const rows = parseInteger(rowsInput.value, "行数 / Row count", 1);
        const stoneLimit = parseInteger(stoneLimitInput.value, "岩の上限 / Stone limit", 0);
        const grid = buildGrid(pattern, rows);
        const solution = optimize(grid, stoneLimit, efficiencyInput.checked);
        showSolution(grid, solution);
    } catch (error) {
        emptyState.hidden = true;
        errorMessage.textContent = error instanceof Error
            ? error.message
            : "計算中にエラーが発生しました。 / An unexpected error occurred.";
        errorMessage.hidden = false;
    }
});

efficiencyInput.addEventListener("change", () => {
    optimizationSummary.textContent = efficiencyInput.checked
        ? "全件カバー → 岩1個あたり被覆数最大化"
        : "全件カバー → 重複数最大化";
});