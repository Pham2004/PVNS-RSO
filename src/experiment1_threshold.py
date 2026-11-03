"""
Thực nghiệm 1: Khảo sát ngưỡng chuyển đổi brute-force sang Regret-2
============================================================================
Mục tiêu: Giải thích tại sao chọn ngưỡng 7 nodes.

Cấu hình qua env:
  DATASET=pdp_100
  TESTCASES=lc101,lr101          (để trống = full)
  SEEDS=42,123,456,789,2024      (để trống = mặc định 5 seeds)
  THRESHOLDS=5,6,7,8,9           (để trống = mặc định 5,6,7,8,9)
"""

import os
import sys
import time
import csv
import numpy as np
import random

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from Simulator.Graph import Graph
from MainAlgo.NewAlgo import NewAlgo
from MainAlgo.ATSP import ATSP
from Simulator.CostCalculationEvent import CostCalculator

DEFAULT_SEEDS = [42, 123, 456, 789, 2024]
DEFAULT_THRESHOLDS = [5, 6, 7, 8, 9]


def patch_atsp_threshold(threshold):
    """Monkey-patch ATSP.run() để thay đổi ngưỡng brute-force/Regret-2."""
    import itertools
    from Simulator.Solution import Solution
    from Simulator.Vehicle import Vehicle
    
    def patched_run(self, tree, evaluation_limit):
        nodes_with_children = [node for node in tree.tree_nodes.values() 
                            if len(node.children) > 1 and node.label >= 0]
        random.shuffle(nodes_with_children)
        self.evaluation_count = 0
        
        for node in nodes_with_children:
            child_subtrees = node.children
            num_children = len(child_subtrees)
            
            if num_children <= 1:
                continue
                
            original_solution = Solution.tree_to_tours(tree)
            original_cost = CostCalculator.calculate(self.graph, original_solution.vehicle_list)
            original_order = list(node.children)
            
            if num_children <= threshold:
                best_cost = original_cost
                best_order = original_order
                permutations = list(itertools.permutations(range(num_children)))
                random.shuffle(permutations)
                
                for perm in permutations:
                    new_order = [child_subtrees[i] for i in perm]
                    temp_order = node.children
                    node.children = new_order
                    solution = Solution.tree_to_tours(tree)
                    if Solution.is_sol_feasible(self.graph, solution.vehicle_list):
                        cost = CostCalculator.calculate(self.graph, solution.vehicle_list)
                        if cost < best_cost:
                            best_cost = cost
                            best_order = list(new_order)
                    node.children = temp_order
                    if self.evaluation_count >= evaluation_limit:
                        break
                if best_cost < original_cost:
                    node.children = best_order
            else:
                tour_indices = []
                unvisited = set(range(num_children))
                depot = node
                while depot.label != 0:
                    depot = depot.parent
                while unvisited:
                    best_regret = -float('inf')
                    best_node_idx = None
                    best_pos = -1
                    best_cost_after_insertion = float('inf')
                    for node_idx in unvisited:
                        insertion_costs = []
                        for pos in range(len(tour_indices) + 1):
                            new_tour_indices = tour_indices.copy()
                            new_tour_indices.insert(pos, node_idx)
                            new_order = [child_subtrees[idx] for idx in new_tour_indices]
                            temp_order = node.children
                            node.children = new_order
                            travel_path = Solution.subtree_to_travel_path(self.graph, depot)
                            cost = Vehicle.cal_total_all_cost(self.graph, travel_path)
                            insertion_costs.append((pos, cost))
                            node.children = temp_order
                        if not insertion_costs:
                            continue
                        insertion_costs.sort(key=lambda x: x[1])
                        if len(insertion_costs) >= 2:
                            regret = insertion_costs[1][1] - insertion_costs[0][1]
                            if (regret > best_regret or 
                                (regret == best_regret and insertion_costs[0][1] < best_cost_after_insertion)):
                                best_regret = regret
                                best_node_idx = node_idx
                                best_pos = insertion_costs[0][0]
                                best_cost_after_insertion = insertion_costs[0][1]
                        elif len(insertion_costs) == 1:
                            if best_node_idx is None or insertion_costs[0][1] < best_cost_after_insertion:
                                best_regret = float('inf')
                                best_node_idx = node_idx
                                best_pos = insertion_costs[0][0]
                                best_cost_after_insertion = insertion_costs[0][1]
                    if best_node_idx is None:
                        break
                    tour_indices.insert(best_pos, best_node_idx)
                    unvisited.remove(best_node_idx)
                if len(tour_indices) == num_children:
                    new_order = [child_subtrees[idx] for idx in tour_indices]
                    node.children = new_order
                    solution = Solution.tree_to_tours(tree)
                    if Solution.is_sol_feasible(self.graph, solution.vehicle_list):
                        cost = CostCalculator.calculate(self.graph, solution.vehicle_list)
                        if cost >= original_cost:
                            node.children = original_order
                    else:
                        node.children = original_order
                else:
                    node.children = original_order
            if self.evaluation_count >= evaluation_limit:
                break
        return tree
    
    ATSP.run = patched_run


def run_single(testcase, folder_path, threshold, seed):
    """Chạy 1 lần: testcase × threshold × seed."""
    random.seed(seed)
    np.random.seed(seed)
    CostCalculator.remove_all_listeners()
    
    file_path = folder_path + f'/{testcase}.txt'
    g = Graph(file_path, cd=0.7, xi=1, kappa=44, p=1.2, A=3.192, mk=3.2, g=9.81,
              cr=0.01, b1=2, b2=2.5, p1=1, p2=1000, psi=737, pi=0.2,
              R=165, eta=0.36, rho=0.85, Q=1000, v=50)
    
    patch_atsp_threshold(threshold)
    
    start_time = time.time()
    lcs = NewAlgo(g, 10)
    sol, cost, energy_cost, penalty_cost = lcs.run()
    elapsed = time.time() - start_time
    
    return {
        'testcase': testcase, 'threshold': threshold, 'seed': seed,
        'best_cost': cost, 'energy_cost': energy_cost,
        'penalty_cost': penalty_cost, 'elapsed_time': elapsed,
        'evaluations': lcs.evaluation_count
    }


def parse_int_list(s, default):
    if not s or not s.strip():
        return default
    return [int(x.strip()) for x in s.split(',') if x.strip()]


def parse_float_list(s, default):
    if not s or not s.strip():
        return default
    return [float(x.strip()) for x in s.split(',') if x.strip()]


def main():
    dataset = os.environ.get('DATASET', 'pdp_100')
    folder_path = os.environ.get('FOLDER_PATH', os.path.join(project_root, 'data', dataset))
    output_dir = os.path.join(project_root, 'results', 'experiment1_threshold')
    os.makedirs(output_dir, exist_ok=True)
    
    thresholds = parse_int_list(os.environ.get('THRESHOLDS', ''), DEFAULT_THRESHOLDS)
    seeds = parse_int_list(os.environ.get('SEEDS', ''), DEFAULT_SEEDS)
    
    testcases_env = os.environ.get('TESTCASES', '').strip()
    if testcases_env:
        testcases = [t.strip() for t in testcases_env.split(',') if t.strip()]
    else:
        testcases = sorted([f[:-4] for f in os.listdir(folder_path) if f.endswith('.txt')])
    
    print("=" * 70)
    print("THỰC NGHIỆM 1: KHẢO SÁT NGƯỠNG BRUTE-FORCE vs REGRET-2")
    print("=" * 70)
    print(f"Thresholds: {thresholds}")
    print(f"Testcases: {len(testcases)} ({testcases[:5]}{'...' if len(testcases) > 5 else ''})")
    print(f"Seeds: {seeds} ({len(seeds)} seeds)")
    total_runs = len(testcases) * len(thresholds) * len(seeds)
    print(f"Tổng số lần chạy: {total_runs}")
    print()
    
    summary_file = os.path.join(output_dir, 'threshold_summary.csv')
    with open(summary_file, 'w', newline='') as f:
        csv.writer(f).writerow(['Testcase', 'Threshold', 'Seed', 'Best_Cost',
                                'Energy_Cost', 'Penalty_Cost', 'Elapsed_Time(s)', 'Evaluations'])
    
    all_results = []
    run_count = 0
    
    for testcase in testcases:
        for threshold in thresholds:
            for seed in seeds:
                run_count += 1
                print(f"[{run_count}/{total_runs}] {testcase} | threshold={threshold} | seed={seed}")
                try:
                    result = run_single(testcase, folder_path, threshold, seed)
                    all_results.append(result)
                    with open(summary_file, 'a', newline='') as f:
                        csv.writer(f).writerow([
                            result['testcase'], result['threshold'], result['seed'],
                            result['best_cost'], result['energy_cost'],
                            result['penalty_cost'], f"{result['elapsed_time']:.2f}",
                            result['evaluations']
                        ])
                    print(f"  -> cost={result['best_cost']:.2f}, time={result['elapsed_time']:.2f}s")
                except Exception as e:
                    print(f"  LỖI: {e}")
    
    # Tổng hợp trung bình ± std
    avg_file = os.path.join(output_dir, 'threshold_average.csv')
    with open(avg_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'Threshold', 'Num_Seeds',
                         'Avg_Best_Cost', 'Std_Best_Cost',
                         'Avg_Energy_Cost', 'Std_Energy_Cost',
                         'Avg_Penalty_Cost', 'Std_Penalty_Cost',
                         'Avg_Time(s)', 'Std_Time(s)', 'Min_Cost', 'Max_Cost'])
        for tc in testcases:
            for th in thresholds:
                runs = [r for r in all_results if r['testcase'] == tc and r['threshold'] == th]
                if runs:
                    costs = [r['best_cost'] for r in runs]
                    writer.writerow([tc, th, len(runs),
                        f"{np.mean(costs):.2f}", f"{np.std(costs):.2f}",
                        f"{np.mean([r['energy_cost'] for r in runs]):.2f}",
                        f"{np.std([r['energy_cost'] for r in runs]):.2f}",
                        f"{np.mean([r['penalty_cost'] for r in runs]):.2f}",
                        f"{np.std([r['penalty_cost'] for r in runs]):.2f}",
                        f"{np.mean([r['elapsed_time'] for r in runs]):.2f}",
                        f"{np.std([r['elapsed_time'] for r in runs]):.2f}",
                        f"{np.min(costs):.2f}", f"{np.max(costs):.2f}"])
    
    print(f"\nKết quả chi tiết: {summary_file}")
    print(f"Kết quả trung bình: {avg_file}")
    print(f"Tổng: {len(all_results)} lần chạy")
    print("HOÀN THÀNH THỰC NGHIỆM 1!")


if __name__ == "__main__":
    main()
