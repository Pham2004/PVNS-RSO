"""
Thực nghiệm 3: Khảo sát ảnh hưởng của vận tốc đến mức tiêu thụ năng lượng
=============================================================================
Mục tiêu: Tối ưu lại tuyến đường cho từng vận tốc.

Vận tốc hiện tại trong code:
  - v = 50 (km/h) — truyền vào qua Graph constructor, dòng 38 trong main.py

Công thức năng lượng (từ Vehicle.py dòng 19):
  T = 1/2 * cd * p * A * v^3  +  (mk + vehicle_load) * g * cr * v
       ^^^^^^^^^^^^^^^^^^^^^^^^    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
       Lực cản khí động (tỷ lệ v³)    Lực cản lăn (tỷ lệ v)
  
  G = xi / (kappa * psi) * (pi * R + T / eta)
  energy = G * distance

  Lưu ý: Thời gian travel_time = dist / v * 60 (Vehicle.py dòng 50)
  => Vận tốc ảnh hưởng đến CẢ năng lượng VÀ penalty (qua time window)

Multi-seed: Mỗi tổ hợp testcase × vận tốc × seed chạy thuật toán riêng.
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
from Simulator.CostCalculationEvent import CostCalculator


# ══════════════════════════════════════════════════════════════════════════
DEFAULT_SEEDS = [42, 123, 456, 789, 2024]
DEFAULT_VELOCITIES = [20, 30, 40, 50, 60, 70, 80]
# ══════════════════════════════════════════════════════════════════════════


def run_single(testcase, folder_path, v, seed, mk=3.2):
    """Tối ưu một lần với vận tốc và seed đã chọn."""
    random.seed(seed)
    np.random.seed(seed)
    CostCalculator.remove_all_listeners()
    file_path = os.path.join(folder_path, f'{testcase}.txt')
    graph = Graph(file_path, cd=0.7, xi=1, kappa=44, p=1.2, A=3.192, mk=mk, g=9.81,
                  cr=0.01, b1=2, b2=2.5, p1=1, p2=1000, psi=737, pi=0.2,
                  R=165, eta=0.36, rho=0.85, Q=1000, v=v)
    start = time.time()
    solution, cost, energy, penalty = NewAlgo(graph, 10).run()
    routes = [list(vehicle.travel_path) for vehicle in solution] if solution else []
    return {'testcase': testcase, 'seed': seed, 'velocity': v,
            'total_energy': energy, 'total_penalty': penalty,
            'total_cost': cost, 'elapsed_time': time.time() - start}, routes


def parse_seeds(seeds_str):
    """Parse chuỗi seeds từ env: '42,123,456' -> [42, 123, 456]"""
    if not seeds_str or not seeds_str.strip():
        return DEFAULT_SEEDS
    return [int(s.strip()) for s in seeds_str.split(',') if s.strip()]


def parse_velocities(value):
    values = DEFAULT_VELOCITIES if not value.strip() else [float(x.strip()) for x in value.split(',') if x.strip()]
    if not values or any(not np.isfinite(x) or x <= 0 for x in values):
        raise ValueError('VELOCITIES phải là danh sách số dương, ví dụ: 30,45,60')
    return list(dict.fromkeys(values))


def main():
    # === CẤU HÌNH ===
    dataset = os.environ.get('DATASET', 'pdp_100')
    folder_path = os.environ.get('FOLDER_PATH', os.path.join(project_root, 'data', dataset))
    output_dir = os.path.join(project_root, 'results', 'experiment3_velocity')
    
    os.makedirs(output_dir, exist_ok=True)
    
    v_values = parse_velocities(os.environ.get('VELOCITIES', ''))
    
    # Testcases: đọc từ env hoặc lấy toàn bộ file .txt trong folder
    testcases_env = os.environ.get('TESTCASES', '').strip()
    if testcases_env:
        testcases = [t.strip() for t in testcases_env.split(',') if t.strip()]
    else:
        testcases = sorted([f[:-4] for f in os.listdir(folder_path) if f.endswith('.txt')])
    
    # Seeds
    seeds = parse_seeds(os.environ.get('SEEDS', ''))
    
    print("=" * 70)
    print("THỰC NGHIỆM 3: KHẢO SÁT ẢNH HƯỞNG CỦA VẬN TỐC XE")
    print("=" * 70)
    print(f"Các giá trị khảo sát: {v_values}")
    print(f"Mốc tính % thay đổi: v={v_values[0]:g} km/h")
    print(f"Tải trọng cố định: mk = 3.2 tấn")
    print(f"Testcases: {testcases}")
    print(f"Seeds: {seeds} ({len(seeds)} seeds)")
    total_runs = len(testcases) * len(seeds) * len(v_values)
    print(f"Tổng số lần chạy thuật toán: {total_runs}")
    print()
    
    # File kết quả chi tiết
    summary_file = os.path.join(output_dir, 'velocity_summary.csv')
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'Seed', 'Velocity(km/h)', 'Total_Energy', 
                         'Total_Penalty', 'Total_Cost', 'Elapsed_Time(s)',
                         'Energy_Change_Pct(%)', 'Penalty_Change_Pct(%)',
                         'Cost_Change_Pct(%)'])
    
    all_results = []
    
    for testcase in testcases:
        print(f"\n{'='*50}")
        print(f"Testcase: {testcase}")
        print(f"{'='*50}")
        
        for seed in seeds:
            baseline = None  # Vận tốc đầu tiên được chọn.
            for v in v_values:
                print(f"  {testcase} | seed={seed} | v={v:g} km/h")
                try:
                    result, routes = run_single(testcase, folder_path, v, seed)
                    if baseline is None:
                        baseline = result
                    for field, base_field in [('energy_change_pct', 'total_energy'),
                                              ('penalty_change_pct', 'total_penalty'),
                                              ('cost_change_pct', 'total_cost')]:
                        base = baseline[base_field]
                        result[field] = ((result[base_field] - base) / base * 100) if base else 0
                    all_results.append(result)
                    with open(summary_file, 'a', newline='') as f:
                        csv.writer(f).writerow([
                            testcase, seed, v, f"{result['total_energy']:.4f}",
                            f"{result['total_penalty']:.4f}", f"{result['total_cost']:.4f}",
                            f"{result['elapsed_time']:.2f}",
                            f"{result['energy_change_pct']:.2f}",
                            f"{result['penalty_change_pct']:.2f}",
                            f"{result['cost_change_pct']:.2f}"])
                    route_file = os.path.join(output_dir, f'{testcase}_v{v:g}_seed{seed}_routes.txt')
                    with open(route_file, 'w') as f:
                        for i, route in enumerate(routes):
                            f.write(f"Vehicle {i}: {' -> '.join(map(str, route))}\n")
                    print(f"    cost={result['total_cost']:.2f}, energy={result['total_energy']:.2f}")
                except Exception as e:
                    print(f"  LỖI (v={v:g}, seed={seed}): {e}")
                    import traceback
                    traceback.print_exc()
    
    # ─── Tổng hợp trung bình ± std qua các seeds ───
    print("\n\n" + "=" * 70)
    print("BẢNG TỔNG HỢP: TRUNG BÌNH ± STD QUA CÁC SEEDS")
    print("=" * 70)
    
    avg_file = os.path.join(output_dir, 'velocity_average.csv')
    with open(avg_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'Velocity(km/h)', 'Num_Seeds',
                         'Avg_Energy', 'Std_Energy',
                         'Avg_Penalty', 'Std_Penalty',
                         'Avg_Total_Cost', 'Std_Total_Cost',
                         'Avg_Energy_Change_Pct(%)', 'Avg_Cost_Change_Pct(%)'])
        
        for testcase in testcases:
            for v in v_values:
                runs = [r for r in all_results 
                       if r['testcase'] == testcase and r['velocity'] == v]
                if runs:
                    energies = [r['total_energy'] for r in runs]
                    penalties = [r['total_penalty'] for r in runs]
                    costs = [r['total_cost'] for r in runs]
                    e_changes = [r['energy_change_pct'] for r in runs]
                    c_changes = [r['cost_change_pct'] for r in runs]
                    
                    writer.writerow([
                        testcase, v, len(runs),
                        f"{np.mean(energies):.4f}", f"{np.std(energies):.4f}",
                        f"{np.mean(penalties):.4f}", f"{np.std(penalties):.4f}",
                        f"{np.mean(costs):.4f}", f"{np.std(costs):.4f}",
                        f"{np.mean(e_changes):.2f}", f"{np.mean(c_changes):.2f}"
                    ])
                    
                    print(f"  {testcase} | v={v:g} | "
                          f"energy={np.mean(energies):.2f}±{np.std(energies):.2f} | "
                          f"penalty={np.mean(penalties):.2f}±{np.std(penalties):.2f} | "
                          f"Δenergy={np.mean(e_changes):+.2f}%")
    
    # ─── Vận tốc tối ưu ───
    print("\n" + "=" * 70)
    print("VẬN TỐC TỐI ƯU CHO MỖI TESTCASE (chi phí tổng trung bình thấp nhất)")
    print("=" * 70)
    
    optimal_file = os.path.join(output_dir, 'optimal_velocity.csv')
    with open(optimal_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'Optimal_Velocity(km/h)', 
                         'Avg_Min_Total_Cost', 'Std_Min_Total_Cost'])
        
        for testcase in testcases:
            best_v = None
            best_avg_cost = float('inf')
            best_std_cost = 0
            
            for v in v_values:
                runs = [r for r in all_results 
                       if r['testcase'] == testcase and r['velocity'] == v]
                if runs:
                    avg_cost = np.mean([r['total_cost'] for r in runs])
                    std_cost = np.std([r['total_cost'] for r in runs])
                    if avg_cost < best_avg_cost:
                        best_avg_cost = avg_cost
                        best_std_cost = std_cost
                        best_v = v
            
            if best_v is not None:
                writer.writerow([testcase, best_v, 
                               f"{best_avg_cost:.2f}", f"{best_std_cost:.2f}"])
                print(f"  {testcase}: v_optimal = {best_v} km/h "
                      f"(avg_cost = {best_avg_cost:.2f}±{best_std_cost:.2f})")
    
    print(f"\nKết quả chi tiết: {summary_file}")
    print(f"Kết quả trung bình: {avg_file}")
    print(f"Vận tốc tối ưu: {optimal_file}")
    print(f"Tổng số lần chạy thành công: {len(all_results)}/{total_runs}")
    if len(all_results) != total_runs:
        raise RuntimeError(f"Thực nghiệm 3 thất bại {total_runs - len(all_results)} lần chạy")
    print("HOÀN THÀNH THỰC NGHIỆM 3!")


if __name__ == "__main__":
    main()
