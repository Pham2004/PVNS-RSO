"""Run only the missing pdp_400, mk=4 testcase/seed pairs from the workflow."""

import argparse
import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_SEEDS = {42, 123, 456, 789}


def requested_pairs(raw):
    pairs = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        testcase, seed_text = line.strip().split("=", 1)
        for seed in seed_text.split(","):
            pairs.append((testcase, int(seed.strip())))
    if len(pairs) != 69 or len(set(pairs)) != 69:
        raise ValueError("Expected exactly 69 distinct testcase/seed pairs")
    if any(seed not in EXPECTED_SEEDS for _, seed in pairs):
        raise ValueError("Unexpected seed in CASE_SEEDS")
    if any(not (ROOT / "data" / "pdp_400" / f"{case}.txt").is_file() for case, _ in pairs):
        raise ValueError("Unknown pdp_400 testcase in CASE_SEEDS")
    return pairs


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    dataset = os.environ.get("DATASET")
    mk = float(os.environ.get("MK", "nan"))
    velocity = float(os.environ.get("VELOCITY", "nan"))
    if (dataset, mk, velocity) != ("pdp_400", 4.0, 50.0):
        raise ValueError("This workflow is fixed to pdp_400, mk=4 t, v=50 km/h")
    pairs = requested_pairs(os.environ.get("CASE_SEEDS", ""))
    print(f"Configured {len(pairs)} missing pairs: pdp_400, mk=4, v=50", flush=True)
    if args.dry_run:
        for testcase, seed in pairs:
            print(testcase, seed)
        return

    from experiment2_payload import run_single

    output = ROOT / "results" / "experiment2_payload"
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "payload_summary.csv"
    failures = []
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Testcase", "Seed", "mk(ton)", "Total_Energy",
                         "Total_Penalty", "Total_Cost", "Elapsed_Time(s)",
                         "Energy_Change_Pct(%)"])
        file.flush()
        for index, (testcase, seed) in enumerate(pairs, 1):
            print(f"[{index}/{len(pairs)}] {testcase}, seed={seed}, mk=4", flush=True)
            try:
                result, routes = run_single(testcase, ROOT / "data" / dataset,
                                            mk, seed, v=velocity)
                writer.writerow([testcase, seed, mk,
                                 f"{result['total_energy']:.4f}",
                                 f"{result['total_penalty']:.4f}",
                                 f"{result['total_cost']:.4f}",
                                 f"{result['elapsed_time']:.2f}", ""])
                file.flush()
                route_path = output / f"{testcase}_mk4_seed{seed}_routes.txt"
                with route_path.open("w", encoding="utf-8") as routes_file:
                    for vehicle, route in enumerate(routes):
                        routes_file.write(f"Vehicle {vehicle}: {' -> '.join(map(str, route))}\n")
            except Exception as exc:
                failures.append((testcase, seed))
                print(f"FAILED {testcase}, seed={seed}: {exc}", flush=True)

    if failures:
        raise RuntimeError(f"{len(failures)} pairs failed: {failures}")
    print(f"Completed all {len(pairs)} missing pairs; results: {csv_path}")


if __name__ == "__main__":
    main()
