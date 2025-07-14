import pandas as pd
from ortools.sat.python import cp_model
from collections import Counter

def space_runs_min_gap_hard(df: pd.DataFrame, min_gap=8) -> pd.DataFrame | None:
    df = df.dropna(subset=["Human", "Dog"]).reset_index(drop=True)
    if df.empty:
        print("⚠️ DataFrame is empty after dropping missing Human or Dog")
        return None

    print(f"Scheduling {len(df)} runs with min_gap={min_gap}")

    human_counts = Counter(df['Human'])
    dog_counts = Counter(df['Dog'])
    print("Human run counts:", human_counts)
    print("Dog run counts:", dog_counts)

    runs = df.to_dict('records')
    n = len(runs)

    model = cp_model.CpModel()
    positions = [model.NewIntVar(0, n - 1, f'pos_{i}') for i in range(n)]
    model.AddAllDifferent(positions)

    human_runs = {}
    dog_runs = {}
    for i, run in enumerate(runs):
        human_runs.setdefault(run['Human'], []).append(i)
        dog_runs.setdefault(run['Dog'], []).append(i)

    def add_hard_min_gap(entity_runs, entity_name):
        for entity, indices in entity_runs.items():
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    r1, r2 = indices[i], indices[j]
                    order = model.NewBoolVar(f'{entity_name}_{entity}_order_{r1}_{r2}')
                    model.Add(positions[r2] - positions[r1] >= min_gap).OnlyEnforceIf(order)
                    model.Add(positions[r1] - positions[r2] >= min_gap).OnlyEnforceIf(order.Not())

    add_hard_min_gap(human_runs, "human")
    add_hard_min_gap(dog_runs, "dog")

    model.Minimize(0)

    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    solver.parameters.max_time_in_seconds = 300  # increase time to 5 minutes

    status = solver.Solve(model)

    print(f"Solver status: {solver.StatusName(status)}")

    if status not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        print(f"❌ No valid schedule found with min_gap={min_gap}.")
        return None

    pos_to_run = [(solver.Value(pos), i) for i, pos in enumerate(positions)]
    pos_to_run.sort(key=lambda x: x[0])
    ordered_runs = [runs[i] for _, i in pos_to_run]

    last_seen_human = {}
    last_seen_dog = {}
    last_human_run_list = []
    last_dog_run_list = []

    for idx, run in enumerate(ordered_runs):
        human = run['Human']
        dog = run['Dog']

        last_human = idx - last_seen_human[human] if human in last_seen_human else None
        last_dog = idx - last_seen_dog[dog] if dog in last_seen_dog else None

        last_human_run_list.append(last_human)
        last_dog_run_list.append(last_dog)

        last_seen_human[human] = idx
        last_seen_dog[dog] = idx

    result_df = pd.DataFrame(ordered_runs)
    result_df['Last Human Run'] = last_human_run_list
    result_df['Last Dog Run'] = last_dog_run_list

    result_df.reset_index(drop=True, inplace=True)
    result_df.index = result_df.index + 1
    result_df.index.name = "Run Number"

    return result_df
