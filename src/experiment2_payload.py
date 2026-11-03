"""
Thực nghiệm 2: Khảo sát ảnh hưởng của tải trọng xe đến mức tiêu thụ năng lượng
=================================================================================
Mục tiêu: Giữ nguyên tuyến đường và vận tốc, thay đổi tải trọng (mk - khối lượng 
xe không tải) để quan sát mức tiêu thụ năng lượng.

Tải trọng hiện tại trong code:
  - mk (khối lượng xe không tải / curb weight) = 3.2 (tấn)
  - vehicle_capacity = 200 (đọc từ file data, dòng 1)

Công thức năng lượng (từ Vehicle.py dòng 19):
  T = 1/2 * cd * p * A * v^3 + (mk + vehicle_load) * g * cr * v
  G = xi / (kappa * psi) * (pi * R + T / eta)
  energy = G * distance

=> mk ảnh hưởng trực tiếp đến T thông qua (mk + vehicle_load) * g * cr * v

Multi-seed: Mỗi seed tạo ra tuyến đường tối ưu khác nhau → tính lại energy 
với tất cả mk trên mỗi tuyến đường → trung bình ± std qua các seeds.
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


def run_experiment_with_seed(testcase, folder_path, mk_values, seed, v=50):
    """
    Chạy thuật toán 1 lần với seed cố định để lấy tuyến đường tối ưu,
    sau đó tính lại năng lượng cho TẤT CẢ giá trị mk trên cùng tuyến đường.
    """
    # === Set seed ===
    random.seed(seed)
    np.random.seed(seed)
    
    CostCalculator.remove_all_listeners()
    
    file_path = folder_path + f'/{testcase}.txt'
    
    # Chạy thuật toán với tham số gốc
    print(f"    Seed={seed}: Đang tìm tuyến đường tối ưu...")
    g_original = Graph(file_path, cd=0.7, xi=1, kappa=44, p=1.2, A=3.192, mk=3.2, g=9.81,
                       cr=0.01, b1=2, b2=2.5, p1=1, p2=1000, psi=737, pi=0.2,
                       R=165, eta=0.36, rho=0.85, Q=1000, v=v)
    
    lcs = NewAlgo(g_original, 10)
    sol, cost, energy_cost_original, penalty_cost_original = lcs.run()
    
    # Lấy tuyến đường tối ưu
    routes = []
    if sol:
        for vehicle in sol:
            routes.append(list(vehicle.travel_path))
    
    print(f"    Seed={seed}: {len(routes)} xe, cost gốc = {cost:.2f}")
    
    # Tính năng lượng cho TẤT CẢ giá trị mk trên cùng tuyến đường
    results = []
    for mk in mk_values:
        g_new = Graph(file_path, cd=0.7, xi=1, kappa=44, p=1.2, A=3.192, mk=mk, g=9.81,
                      cr=0.01, b1=2, b2=2.5, p1=1, p2=1000, psi=737, pi=0.2,
                      R=165, eta=0.36, rho=0.85, Q=1000, v=v)
        
        total_energy = 0
        total_penalty = 0
        
        for route in routes:
            total_energy += Vehicle.cal_total_engine_energy_consumption(g_new, route)
            total_penalty += Vehicle.cal_total_penalty(g_new, route)
        
        results.append({
            'testcase': testcase,
            'seed': seed,
            'mk': mk,
            'total_energy': total_energy,
            'total_penalty': total_penalty,
            'total_cost': total_energy + total_penalty,
            'energy_change_pct': ((total_energy - energy_cost_original) / energy_cost_original * 100) 
                                  if energy_cost_original > 0 else 0
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
    output_dir = os.path.join(project_root, 'results', 'experiment2_payload')
    
    os.makedirs(output_dir, exist_ok=True)
    
    mk_values = [2.0, 2.5, 3.2, 4.0, 5.0, 6.5, 8.0]
    
    # Testcases
    testcases_env = os.environ.get('TESTCASES', '').strip()
    if testcases_env:
        testcases = [t.strip() for t in testcases_env.split(',') if t.strip()]
    else:
        testcases = ["lc101", "lc201", "lr101", "lr201", "lrc101", "lrc201"]
    
    # Seeds
    seeds = parse_seeds(os.environ.get('SEEDS', ''))
    
    print("=" * 70)
    print("THỰC NGHIỆM 2: KHẢO SÁT ẢNH HƯỞNG CỦA TẢI TRỌNG XE (mk)")
    print("=" * 70)
    print(f"Tải trọng hiện tại: mk = 3.2 tấn")
    print(f"Các giá trị khảo sát: {mk_values}")
    print(f"Vận tốc cố định: v = 50 km/h")
    print(f"Testcases: {testcases}")
    print(f"Seeds: {seeds} ({len(seeds)} seeds)")
    print()
    
    # File kết quả chi tiết
    summary_file = os.path.join(output_dir, 'payload_summary.csv')
    with open(summary_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'Seed', 'mk(ton)', 'Total_Energy', 'Total_Penalty',
                         'Total_Cost', 'Energy_Change_Pct(%)'])
    
    all_results = []
    
    for testcase in testcases:
        print(f"\n{'='*50}")
        print(f"Testcase: {testcase}")
        print(f"{'='*50}")
        
        for seed in seeds:
            try:
                results, routes = run_experiment_with_seed(
                    testcase, folder_path, mk_values, seed)
                all_results.extend(results)
                
                # Ghi vào CSV
                with open(summary_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    for r in results:
                        writer.writerow([
                            r['testcase'], r['seed'], r['mk'],
                            f"{r['total_energy']:.4f}",
                            f"{r['total_penalty']:.4f}", f"{r['total_cost']:.4f}",
                            f"{r['energy_change_pct']:.2f}"
                        ])
                
                # Lưu tuyến đường
                route_file = os.path.join(output_dir, f'{testcase}_seed{seed}_routes.txt')
                with open(route_file, 'w') as f:
                    for i, route in enumerate(routes):
                        f.write(f"Vehicle {i}: {' -> '.join(map(str, route))}\n")
                        
                # In tóm tắt cho seed này
                for r in results:
                    print(f"    mk={r['mk']:.1f}t -> energy={r['total_energy']:.2f}, "
                          f"change={r['energy_change_pct']:+.2f}%")
                
            except Exception as e:
                print(f"  LỖI (seed={seed}): {e}")
                import traceback
                traceback.print_exc()
    
    # ─── Tổng hợp trung bình ± std qua các seeds ───
    print("\n\n" + "=" * 70)
    print("BẢNG TỔNG HỢP: TRUNG BÌNH ± STD QUA CÁC SEEDS")
    print("=" * 70)
    
    avg_file = os.path.join(output_dir, 'payload_average.csv')
    with open(avg_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Testcase', 'mk(ton)', 'Num_Seeds',
                         'Avg_Energy', 'Std_Energy',
                         'Avg_Penalty', 'Std_Penalty',
                         'Avg_Total_Cost', 'Std_Total_Cost',
                         'Avg_Energy_Change_Pct(%)'])
        
        for testcase in testcases:
            for mk in mk_values:
                runs = [r for r in all_results 
                       if r['testcase'] == testcase and r['mk'] == mk]
                if runs:
                    energies = [r['total_energy'] for r in runs]
                    penalties = [r['total_penalty'] for r in runs]
                    costs = [r['total_cost'] for r in runs]
                    changes = [r['energy_change_pct'] for r in runs]
                    
                    writer.writerow([
                        testcase, mk, len(runs),
                        f"{np.mean(energies):.4f}", f"{np.std(energies):.4f}",
                        f"{np.mean(penalties):.4f}", f"{np.std(penalties):.4f}",
                        f"{np.mean(costs):.4f}", f"{np.std(costs):.4f}",
                        f"{np.mean(changes):.2f}"
                    ])
                    
                    print(f"  {testcase} | mk={mk:.1f}t | "
                          f"energy={np.mean(energies):.2f}±{np.std(energies):.2f} | "
                          f"Δ={np.mean(changes):+.2f}%")
    
    print(f"\nKết quả chi tiết: {summary_file}")
    print(f"Kết quả trung bình: {avg_file}")
    print(f"Tổng số lần chạy thuật toán: {len(testcases)} testcases × {len(seeds)} seeds "
          f"= {len(testcases) * len(seeds)} lần")
    print("HOÀN THÀNH THỰC NGHIỆM 2!")


if __name__ == "__main__":
    main()
