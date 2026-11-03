"""
Thực nghiệm 3: Khảo sát ảnh hưởng của vận tốc đến mức tiêu thụ năng lượng
=============================================================================
Mục tiêu: Giữ nguyên tuyến đường và tải trọng, thay đổi vận tốc.

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

Multi-seed: Mỗi seed tạo ra tuyến đường tối ưu khác nhau → tính lại energy + 
penalty với tất cả v trên mỗi tuyến đường → trung bình ± std qua các seeds.
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
from Simulator.Vehicle import Vehicle
from Simulator.Solution import Solution
from MainAlgo.NewAlgo import NewAlgo
from Simulator.CostCalculationEvent import CostCalculator


# ══════════════════════════════════════════════════════════════════════════
DEFAULT_SEEDS = [42, 123, 456, 789, 2024]
# ══════════════════════════════════════════════════════════════════════════


def run_experiment_with_seed(testcase, folder_path, v_values, seed, mk=3.2):
    """
    Chạy thuật toán 1 lần với seed cố định để lấy tuyến đường tối ưu,
    sau đó tính lại energy + penalty cho TẤT CẢ giá trị vận tốc.
    """
    # === Set seed ===
    random.seed(seed)
    np.random.seed(seed)
    
    CostCalculator.remove_all_listeners()
    
    file_path = folder_path + f'/{testcase}.txt'
    
    # Chạy thuật toán MỘT LẦN với tham số gốc (v=50)
    print(f"    Seed={seed}: Đang tìm tuyến đường tối ưu (v=50)...")
    g_original = Graph(file_path, cd=0.7, xi=1, kappa=44, p=1.2, A=3.192, mk=mk, g=9.81,
                       cr=0.01, b1=2, b2=2.5, p1=1, p2=1000, psi=737, pi=0.2,
                       R=165, eta=0.36, rho=0.85, Q=1000, v=50)
    
    lcs = NewAlgo(g_original, 10)
    sol, cost, energy_cost_original, penalty_cost_original = lcs.run()
    
    # Lấy tuyến đường tối ưu
    routes = []
    if sol:
        for vehicle in sol:
            routes.append(list(vehicle.travel_path))
    
    print(f"    Seed={seed}: {len(routes)} xe, cost gốc = {cost:.2f} "
          f"(energy={energy_cost_original:.2f}, penalty={penalty_cost_original:.2f})")
    
    # Tính energy + penalty cho TẤT CẢ vận tốc trên CÙNG tuyến đường
    results = []
    for v in v_values:
        g_new = Graph(file_path, cd=0.7, xi=1, kappa=44, p=1.2, A=3.192, mk=mk, g=9.81,
                      cr=0.01, b1=2, b2=2.5, p1=1, p2=1000, psi=737, pi=0.2,
                      R=165, eta=0.36, rho=0.85, Q=1000, v=v)
        
        total_energy = 0
        total_penalty = 0
        
        for route in routes:
            total_energy += Vehicle.cal_total_engine_energy_consumption(g_new, route)
            total_penalty += Vehicle.cal_total_penalty(g_new, route)
        
        total_cost = total_energy + total_penalty
        
        results.append({
            'testcase': testcase,
            'seed': seed,
            'velocity': v,
            'total_energy': total_energy,
            'total_penalty': total_penalty,
            'total_cost': total_cost,
            'energy_change_pct': ((total_energy - energy_cost_original) / energy_cost_original * 100) 
                                  if energy_cost_original > 0 else 0,
            'penalty_change_pct': ((total_penalty - penalty_cost_original) / penalty_cost_original * 100) 
                                   if penalty_cost_original > 0 else 0,
            'cost_change_pct': ((total_cost - cost) / cost * 100) if cost > 0 else 0
        })
    
    return results, routes


def parse_seeds(seeds_str):
    """Parse chuỗi seeds từ env: '42,123,456' -> [42, 123, 456]"""
    if not seeds_str or not seeds_str.strip():
        return DEFAULT_SEEDS
    return [int(s.strip()) for s in seeds_str.split(',') if s.strip()]


def main():
    # === CẤU HÌNH ===
    dataset = os.environ.get('DATASET', 'pdp_100')
    folder_path = os.environ.get('FOLDER_PATH', os.path.join(project_root, 'data', dataset))
    output_dir = os.path.join(project_root, 'results', 'experiment3_velocity')
    
    os.makedirs(output_dir, exist_ok=True)
    
    v_values = [20, 30, 40, 50, 60, 70, 80]
    
    # Testcases
    testcases_env = os.environ.get('TESTCASES', '').strip()
    if testcases_env:
        testcases = [t.strip() for t in testcases_env.split(',') if t.strip()]
    else:
        testcases = ["lc101", "lc201", "lr101", "lr201", "lrc101", "lrc201"]
    
    # Seeds
    seeds = parse_seeds(os.environ.get('SEEDS', ''))
    
    print("=" * 70)
    print("THỰC NGHIỆM 3: KHẢO SÁT ẢNH HƯỞNG CỦA VẬN TỐC XE")
    print("=" * 70)
    print(f"Vận tốc hiện tại: v = 50 km/h")
    print(f"Các giá trị khảo sát: {v_values}")
    print(f"Tải trọng cố định: mk = 3.2 tấn")
    print(f"Testcases: {testcases}")
    print(f"Seeds: {seeds} ({len(seeds)} seeds)")
    print()
    
    # File kết quả chi tiết
    summary_file = os.path.join(output_dir, 'velocity_summary.csv')
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'Seed', 'Velocity(km/h)', 'Total_Energy', 
                         'Total_Penalty', 'Total_Cost', 
                         'Energy_Change_Pct(%)', 'Penalty_Change_Pct(%)',
                         'Cost_Change_Pct(%)'])
    
    all_results = []
    
    for testcase in testcases:
        print(f"\n{'='*50}")
        print(f"Testcase: {testcase}")
        print(f"{'='*50}")
        
        for seed in seeds:
            try:
                results, routes = run_experiment_with_seed(
                    testcase, folder_path, v_values, seed)
                all_results.extend(results)
                
                # Ghi vào CSV
                with open(summary_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    for r in results:
                        writer.writerow([
                            r['testcase'], r['seed'], r['velocity'],
                            f"{r['total_energy']:.4f}",
                            f"{r['total_penalty']:.4f}", f"{r['total_cost']:.4f}",
                            f"{r['energy_change_pct']:.2f}", 
                            f"{r['penalty_change_pct']:.2f}",
                            f"{r['cost_change_pct']:.2f}"
                        ])
                
                # Lưu tuyến đường
                route_file = os.path.join(output_dir, f'{testcase}_seed{seed}_routes.txt')
                with open(route_file, 'w') as f:
                    for i, route in enumerate(routes):
                        f.write(f"Vehicle {i}: {' -> '.join(map(str, route))}\n")
                
                # In tóm tắt
                for r in results:
                    print(f"    v={r['velocity']:3d} -> energy={r['total_energy']:12.2f}, "
                          f"penalty={r['total_penalty']:12.2f}, "
                          f"Δenergy={r['energy_change_pct']:+.2f}%")
                    
            except Exception as e:
                print(f"  LỖI (seed={seed}): {e}")
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
                    
                    print(f"  {testcase} | v={v:3d} | "
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
    print(f"Tổng số lần chạy thuật toán: {len(testcases)} testcases × {len(seeds)} seeds "
          f"= {len(testcases) * len(seeds)} lần")
    print("HOÀN THÀNH THỰC NGHIỆM 3!")


if __name__ == "__main__":
    main()
