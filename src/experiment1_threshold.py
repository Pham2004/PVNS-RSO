"""
Thực nghiệm 1: Khảo sát ngưỡng chuyển đổi brute-force sang Regret-2
============================================================================
Mục tiêu: Giải thích tại sao chọn ngưỡng 7 nodes.
Chạy thêm với các ngưỡng: 5, 6, 8, 9 (so sánh với ngưỡng gốc 7).

Cách hoạt động:
- Monkey-patch giá trị ngưỡng trong ATSP.run() trước khi chạy thuật toán
- Chạy cùng tập testcase với mỗi ngưỡng
- Mỗi cấu hình chạy với nhiều seed để đảm bảo tính thống kê
- Ghi lại: best_cost, energy_cost, penalty_cost, thời gian chạy, seed
"""

import os
import sys
import time
import csv
import numpy as np
import random

# Thiết lập đường dẫn
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'src'))

from Simulator.Graph import Graph
from MainAlgo.NewAlgo import NewAlgo
from MainAlgo.ATSP import ATSP
from Simulator.CostCalculationEvent import CostCalculator


# ══════════════════════════════════════════════════════════════════════════
# Seeds mặc định — ít nhất 5 seeds cho tính thống kê
# ══════════════════════════════════════════════════════════════════════════
DEFAULT_SEEDS = [42, 123, 456, 789, 2024]


def patch_atsp_threshold(threshold):
    """
    Monkey-patch phương thức ATSP.run() để thay đổi ngưỡng chuyển đổi
    từ brute-force sang Regret-2.
    
    Ngưỡng gốc: 7 (dòng 53 trong ATSP.py: `if num_children <= 7`)
    """
    import itertools
    from Simulator.Solution import Solution
    from Simulator.Vehicle import Vehicle
    
    def patched_run(self, tree, evaluation_limit):
        nodes_with_children = [node for node in tree.tree_nodes.values() 
                            if len(node.children) > 1 and node.label >= 0]
        random.shuffle(nodes_with_children)
        improved = False
        self.evaluation_count = 0
        
        for node in nodes_with_children:
            child_subtrees = node.children
            num_children = len(child_subtrees)
            
            if num_children <= 1:
                continue
                
            original_solution = Solution.tree_to_tours(tree)
            original_cost = CostCalculator.calculate(self.graph, original_solution.vehicle_list)
            original_order = list(node.children)
            
            # === NGƯỠNG ĐƯỢC THAY ĐỔI TẠI ĐÂY ===
            if num_children <= threshold:
                # Brute-force: duyệt hoán vị
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
                # Regret-2 heuristic
                tour_indices = []
                unvisited = set(range(num_children))
                
                depot = node
                while (depot.label != 0):
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
    
    # Áp dụng monkey-patch
    ATSP.run = patched_run
    print(f"  [PATCH] Đã thay đổi ngưỡng ATSP thành {threshold}")


def run_single_experiment(testcase, folder_path, threshold, seed, v=50):
    """Chạy một lần thực nghiệm với ngưỡng và seed cho trước."""
    # === Set seed cho tính tái lập ===
    random.seed(seed)
    np.random.seed(seed)
    
    CostCalculator.remove_all_listeners()
    
    file_path = folder_path + f'/{testcase}.txt'
    
    g = Graph(file_path, cd=0.7, xi=1, kappa=44, p=1.2, A=3.192, mk=3.2, g=9.81,
              cr=0.01, b1=2, b2=2.5, p1=1, p2=1000, psi=737, pi=0.2,
              R=165, eta=0.36, rho=0.85, Q=1000, v=v)
    
    # Patch ngưỡng
    patch_atsp_threshold(threshold)
    
    start_time = time.time()
    lcs = NewAlgo(g, 10)
    sol, cost, energy_cost, penalty_cost = lcs.run()
    elapsed = time.time() - start_time
    
    return {
        'testcase': testcase,
        'threshold': threshold,
        'seed': seed,
        'best_cost': cost,
        'energy_cost': energy_cost,
        'penalty_cost': penalty_cost,
        'elapsed_time': elapsed,
        'evaluations': lcs.evaluation_count
    }


def parse_seeds(seeds_str):
    """Parse chuỗi seeds từ env: '42,123,456' -> [42, 123, 456]"""
    if not seeds_str or not seeds_str.strip():
        return DEFAULT_SEEDS
    return [int(s.strip()) for s in seeds_str.split(',') if s.strip()]


def main():
    # === CẤU HÌNH ===
    dataset = os.environ.get('DATASET', 'pdp_100')
    folder_path = os.environ.get('FOLDER_PATH', os.path.join(project_root, 'data', dataset))
    output_dir = os.path.join(project_root, 'results', 'experiment1_threshold')
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Ngưỡng cần khảo sát
    thresholds = [5, 6, 7, 8, 9]
    
    # Testcases
    testcases_env = os.environ.get('TESTCASES', '').strip()
    if testcases_env:
        testcases = [t.strip() for t in testcases_env.split(',') if t.strip()]
    else:
        testcases = ["lc101", "lc201", "lr101", "lr201", "lrc101", "lrc201"]
    
    # Seeds — ít nhất 5 seeds cho tính thống kê
    seeds = parse_seeds(os.environ.get('SEEDS', ''))
    
    print("=" * 70)
    print("THỰC NGHIỆM 1: KHẢO SÁT NGƯỠNG CHUYỂN ĐỔI BRUTE-FORCE vs REGRET-2")
    print("=" * 70)
    print(f"Ngưỡng khảo sát: {thresholds}")
    print(f"Testcases: {testcases}")
    print(f"Seeds: {seeds} ({len(seeds)} seeds)")
    print()
    
    # File kết quả chi tiết — mỗi dòng = 1 lần chạy (testcase × threshold × seed)
    summary_file = os.path.join(output_dir, 'threshold_summary.csv')
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'Threshold', 'Seed', 'Best_Cost', 'Energy_Cost', 
                         'Penalty_Cost', 'Elapsed_Time(s)', 'Evaluations'])
    
    all_results = []
    
    for testcase in testcases:
        print(f"\n{'='*60}")
        print(f"Testcase: {testcase}")
        print(f"{'='*60}")
        
        for threshold in thresholds:
            for seed in seeds:
                print(f"\n--- Ngưỡng={threshold}, Seed={seed} ---")
                
                try:
                    result = run_single_experiment(testcase, folder_path, threshold, seed)
                    all_results.append(result)
                    
                    # Ghi ngay vào CSV (tránh mất dữ liệu nếu crash)
                    with open(summary_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            result['testcase'], result['threshold'], result['seed'],
                            result['best_cost'], result['energy_cost'],
                            result['penalty_cost'], f"{result['elapsed_time']:.2f}",
                            result['evaluations']
                        ])
                    
                    print(f"  Kết quả: cost={result['best_cost']:.2f}, "
                          f"energy={result['energy_cost']:.2f}, "
                          f"penalty={result['penalty_cost']:.2f}, "
                          f"time={result['elapsed_time']:.2f}s")
                    
                except Exception as e:
                    print(f"  LỖI: {e}")
                    import traceback
                    traceback.print_exc()
    
    # ─── Tạo bảng tổng hợp trung bình ± std qua các seeds ───
    print("\n\n" + "=" * 70)
    print("BẢNG TỔNG HỢP: TRUNG BÌNH ± STD QUA CÁC SEEDS")
    print("=" * 70)
    
    avg_file = os.path.join(output_dir, 'threshold_average.csv')
    with open(avg_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'Threshold', 'Num_Seeds',
                         'Avg_Best_Cost', 'Std_Best_Cost',
                         'Avg_Energy_Cost', 'Std_Energy_Cost',
                         'Avg_Penalty_Cost', 'Std_Penalty_Cost',
                         'Avg_Elapsed_Time(s)', 'Std_Elapsed_Time(s)',
                         'Best_Cost_Min', 'Best_Cost_Max'])
        
        for testcase in testcases:
            for threshold in thresholds:
                runs = [r for r in all_results 
                       if r['testcase'] == testcase and r['threshold'] == threshold]
                if runs:
                    costs = [r['best_cost'] for r in runs]
                    energies = [r['energy_cost'] for r in runs]
                    penalties = [r['penalty_cost'] for r in runs]
                    times = [r['elapsed_time'] for r in runs]
                    
                    writer.writerow([
                        testcase, threshold, len(runs),
                        f"{np.mean(costs):.2f}", f"{np.std(costs):.2f}",
                        f"{np.mean(energies):.2f}", f"{np.std(energies):.2f}",
                        f"{np.mean(penalties):.2f}", f"{np.std(penalties):.2f}",
                        f"{np.mean(times):.2f}", f"{np.std(times):.2f}",
                        f"{np.min(costs):.2f}", f"{np.max(costs):.2f}"
                    ])
                    
                    print(f"  {testcase} | threshold={threshold} | "
                          f"cost={np.mean(costs):.2f}±{np.std(costs):.2f} | "
                          f"time={np.mean(times):.2f}±{np.std(times):.2f}s | "
                          f"[{np.min(costs):.2f} — {np.max(costs):.2f}]")
    
    print(f"\nKết quả chi tiết: {summary_file}")
    print(f"Kết quả trung bình: {avg_file}")
    print(f"Tổng số lần chạy: {len(all_results)} "
          f"({len(testcases)} testcases × {len(thresholds)} thresholds × {len(seeds)} seeds)")
    print("HOÀN THÀNH THỰC NGHIỆM 1!")


if __name__ == "__main__":
    main()
