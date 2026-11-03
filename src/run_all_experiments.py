"""
Script tổng hợp: Chạy tất cả 3 thực nghiệm (Multi-Seed)
============================================================
Cách sử dụng:
  cd e:/PVNS-RSO/src
  
  # Chạy tất cả (5 seeds mặc định: 42, 123, 456, 789, 2024)
  python run_all_experiments.py
  
  # Chỉ chạy thực nghiệm 1
  python run_all_experiments.py --exp 1
  
  # Chạy thực nghiệm 2 và 3
  python run_all_experiments.py --exp 2 3
  
  # Tùy chỉnh seeds
  python run_all_experiments.py --seeds 42 123 456 789 2024 1234 5678
  
  # Tùy chỉnh dataset
  python run_all_experiments.py --dataset pdp_200

Environment variables (cho GitHub Actions):
  DATASET=pdp_100
  TESTCASES=lc101,lr101
  SEEDS=42,123,456,789,2024
"""

import sys
import os
import argparse
import time


def main():
    parser = argparse.ArgumentParser(description='Chạy các thực nghiệm PVNS-RSO (Multi-Seed)')
    parser.add_argument('--exp', nargs='+', type=int, choices=[1, 2, 3],
                       default=[1, 2, 3],
                       help='Chọn thực nghiệm cần chạy (1, 2, 3 hoặc kết hợp)')
    parser.add_argument('--seeds', nargs='+', type=int,
                       default=None,
                       help='Danh sách seeds (mặc định: 42 123 456 789 2024)')
    parser.add_argument('--dataset', type=str, default=None,
                       help='Bộ dữ liệu (pdp_100, pdp_200, pdp_400)')
    parser.add_argument('--testcases', nargs='+', type=str, default=None,
                       help='Danh sách testcases')
    args = parser.parse_args()
    
    # Thiết lập env từ CLI args (ưu tiên CLI > env > mặc định)
    if args.seeds:
        os.environ['SEEDS'] = ','.join(str(s) for s in args.seeds)
    if args.dataset:
        os.environ['DATASET'] = args.dataset
    if args.testcases:
        os.environ['TESTCASES'] = ','.join(args.testcases)
    
    seeds_display = os.environ.get('SEEDS', '42,123,456,789,2024')
    dataset_display = os.environ.get('DATASET', 'pdp_100')
    
    total_start = time.time()
    
    print("╔" + "═" * 68 + "╗")
    print("║" + "  PVNS-RSO: BỘ THỰC NGHIỆM BỔ SUNG (Multi-Seed)  ".center(68) + "║")
    print("╠" + "═" * 68 + "╣")
    print("║" + f"  Experiments: {args.exp}".ljust(68) + "║")
    print("║" + f"  Seeds: {seeds_display}".ljust(68) + "║")
    print("║" + f"  Dataset: {dataset_display}".ljust(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    if 1 in args.exp:
        print("\n" + "█" * 70)
        print("█  THỰC NGHIỆM 1: Ngưỡng chuyển đổi Brute-force / Regret-2          █")
        print("█" * 70)
        try:
            from experiment1_threshold import main as exp1_main
            exp1_main()
        except Exception as e:
            print(f"LỖI thực nghiệm 1: {e}")
            import traceback
            traceback.print_exc()
    
    if 2 in args.exp:
        print("\n" + "█" * 70)
        print("█  THỰC NGHIỆM 2: Ảnh hưởng tải trọng xe (mk)                       █")
        print("█" * 70)
        try:
            from experiment2_payload import main as exp2_main
            exp2_main()
        except Exception as e:
            print(f"LỖI thực nghiệm 2: {e}")
            import traceback
            traceback.print_exc()
    
    if 3 in args.exp:
        print("\n" + "█" * 70)
        print("█  THỰC NGHIỆM 3: Ảnh hưởng vận tốc xe (v)                           █")
        print("█" * 70)
        try:
            from experiment3_velocity import main as exp3_main
            exp3_main()
        except Exception as e:
            print(f"LỖI thực nghiệm 3: {e}")
            import traceback
            traceback.print_exc()
    
    total_elapsed = time.time() - total_start
    print(f"\n\n{'='*70}")
    print(f"TỔNG THỜI GIAN CHẠY: {total_elapsed:.2f}s ({total_elapsed/60:.1f} phút)")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
