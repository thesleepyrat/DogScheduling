import pandas as pd
from ortools.sat.python import cp_model
from collections import Counter

def space_runs_min_gap_hard(df: pd.DataFrame, min_gap=8, time_limit_seconds=120) -> pd.DataFrame | None:
    print(f"📄 Starting schedule: {len(df)} rows (before cleaning)")

    df = df.dropna(subset=["Human", "Dog", "Judge"]).reset_index(drop=True)
    print(f"🧼 Rows after dropping NaNs: {len(df)}")

    # Validate Judge ≠ Human
    for i, row in df.iterrows():
        if row['Human'] == row['Judge']:
            print(f"❌ Row {i + 2}: Judge '{row['Judge']}' == Human '{row['Human']}' — skipping sheet.")
            return None

    if df.empty:
        print("⚠️ DataFrame is empty after validation.")
        return None

    print(f"✅ Proceeding with scheduling {len(df)} valid runs")

    runs = df.to_dict('records')
    n = len(runs)

    model = cp_model.CpModel()
    positions = [model.NewIntVar(0, n - 1, f'pos_{i}') for i in range(n)]
    model.AddAllDifferent(positions)

    # Group runs by entities
    human_runs = {}
    dog_runs = {}
    judge_runs = {}

    for i, run in enumerate(runs):
        human_runs.setdefault(run['Human'], []).append(i)
        dog_runs.setdefault(run['Dog'], []).append(i)
        judge_runs.setdefault(run['Judge'], []).append(i)

    def add_hard_min_gap(entity_runs, label):
        for entity, indices in entity_runs.items():
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    r1, r2 = indices[i], indices[j]
                    order = model.NewBoolVar(f'{label}_{entity}_order_{r1}_{r2}')
                    model.Add(positions[r2] - positions[r1] >= min_gap).OnlyEnforceIf(order)
                    model.Add(positions[r1] - positions[r2] >= min_gap).OnlyEnforceIf(order.Not())

    add_hard_min_gap(human_runs, "human")
    add_hard_min_gap(dog_runs, "dog")

    # Soft min_gap for judges (penalize if too close)
    soft_gap_violations = []
    for judge, indices in judge_runs.items():
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                r1, r2 = indices[i], indices[j]
                abs_diff = model.NewIntVar(0, n, f'abs_judge_{r1}_{r2}')
                model.AddAbsEquality(abs_diff, positions[r1] - positions[r2])
                is_violation = model.NewBoolVar(f'judge_violation_{r1}_{r2}')
                model.Add(abs_diff < min_gap).OnlyEnforceIf(is_violation)
                model.Add(abs_diff >= min_gap).OnlyEnforceIf(is_violation.Not())
                soft_gap_violations.append(is_violation)

    # Minimize soft violations
    model.Minimize(sum(soft_gap_violations))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.log_search_progress = False

    status = solver.Solve(model)
    print(f"Solver status: {solver.StatusName(status)}")

    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        print(f"❌ No valid schedule found with min_gap={min_gap}.")
        return None

    pos_to_run = [(solver.Value(pos), i) for i, pos in enumerate(positions)]
    pos_to_run.sort()
    ordered_runs = [runs[i] for _, i in pos_to_run]

    # Track last seen
    last_seen_human = {}
    last_seen_dog = {}
    last_seen_judge = {}
    last_human_run_list = []
    last_dog_run_list = []
    last_judge_run_list = []

    for idx, run in enumerate(ordered_runs):
        human = run['Human']
        dog = run['Dog']
        judge = run['Judge']

        last_human = idx - last_seen_human[human] if human in last_seen_human else None
        last_dog = idx - last_seen_dog[dog] if dog in last_seen_dog else None
        last_judge = idx - last_seen_judge[judge] if judge in last_seen_judge else None

        last_human_run_list.append(last_human)
        last_dog_run_list.append(last_dog)
        last_judge_run_list.append(last_judge)

        last_seen_human[human] = idx
        last_seen_dog[dog] = idx
        last_seen_judge[judge] = idx

    result_df = pd.DataFrame(ordered_runs)
    result_df['Last Human Run'] = last_human_run_list
    result_df['Last Dog Run'] = last_dog_run_list
    result_df['Last Judge Run'] = last_judge_run_list

    result_df.reset_index(drop=True, inplace=True)
    result_df.index = result_df.index + 1
    result_df.index.name = "Run Number"

    return result_df


def find_max_feasible_gap(df: pd.DataFrame, max_gap=8, min_gap=1, time_limit=10) -> int:
    left = min_gap
    right = max_gap
    best_gap = min_gap

    while left <= right:
        mid = (left + right) // 2
        print(f"🔍 Trying min_gap={mid}...")
        try:
            result_df = space_runs_min_gap_hard(df.copy(), min_gap=mid, time_limit_seconds=time_limit)
            if result_df is not None:
                print(f"✅ min_gap={mid} is feasible")
                best_gap = mid
                left = mid + 1
            else:
                print(f"❌ min_gap={mid} is NOT feasible")
                right = mid - 1
        except Exception as e:
            print(f"💥 Error at gap {mid}: {e}")
            right = mid - 1

    print(f"🎯 Max feasible min_gap: {best_gap}")
    return best_gap
