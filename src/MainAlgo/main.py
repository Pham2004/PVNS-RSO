from Simulator.Graph import Graph
from MainAlgo.NewAlgo import NewAlgo

import os
import sys
import numpy as np
import random

from itertools import islice

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)


def split_list(lst, n):
    lst_iter = iter(lst)
    size = len(lst)
    return [list(islice(lst_iter, size//n + (1 if i < size%n else 0))) 
            for i in range(n)]

def solve(testcase, folder_path, output_dir):
    """
    Giải quyết một trường hợp thử nghiệm và lưu evaluation_logs.
    
    Args:
        testcase: Tên file dữ liệu test
        output_dir: Thư mục lưu evaluation_logs
        
    Returns:
        dict: Chứa testcase và evaluation_logs
    """
    # Điều chỉnh đường dẫn cho môi trường Kaggle
    file_path = folder_path + f'/{testcase}.txt'
    
    # Khởi tạo đồ thị với các tham số
    g = Graph(file_path, cd=0.7, xi=1, kappa=44, p=1.2, A=3.192, mk=3.2, g=9.81, 
              cr=0.01, b1=2, b2=2.5, p1=1, p2=1000, psi=737, pi=0.2, 
              R=165, eta=0.36, rho=0.85, Q=1000, v = 50)
    
    # Chạy thuật toán
    lcs = NewAlgo(g, 10)
    sol, cost, energy_cost, penalty_cost = lcs.run()
    
    # Lưu kết quả
    result = {
        'test': testcase,
        'evaluation_logs': lcs.evaluation_logs,
        'energy_cost': energy_cost,
        'penalty_cost': penalty_cost
    }
    
    # Ghi evaluation_logs vào file
    save_result(result, output_dir)
    
    return result

def save_result(result, output_dir):
    """
    Lưu evaluation_logs vào file.
    
    Args:
        result: Dictionary chứa testcase và evaluation_logs
        output_dir: Thư mục lưu kết quả
    """
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Lưu nhật ký đánh giá
    eval_log_file = os.path.join(output_dir, f"{result['test']}_NewAlgo_evaluation_log.txt")
    with open(eval_log_file, 'w') as f:
        f.write("Evaluation Count,Elapsed Time (s),Best Cost\n")
        for log in result['evaluation_logs']:
            f.write(f"{log['evaluation_count']},{log['elapsed_time']:.5f},{log['best_cost']}\n")
        f.write(f"energy_cost:{result['energy_cost']}\n")
        f.write(f"penalty_cost:{result['penalty_cost']}\n")
        
    print(f"Đã lưu nhật ký đánh giá vào file {eval_log_file}")

def run_experiments(testcases=None, folder_path=None, output_dir=None):
    """
    Chạy thí nghiệm trên nhiều testcase và lưu evaluation_logs.
    
    Args:
        testcases: Danh sách testcase cần chạy
        output_dir: Thư mục lưu kết quả
    """
    # Thiết lập seed cho tính nhất quán
    #random.seed(78)
    #np.random.seed(78)
    
    print(f"Bắt đầu chạy {len(testcases)} testcase")
    
    # Chạy thí nghiệm
    for testcase in testcases[0:1]:
        print(f"\n{'='*50}")
        print(f"Đang chạy testcase {testcase}")
        print(f"{'='*50}\n")
        
        try:
            solve(testcase, folder_path, output_dir)
        except Exception as e:
            print(f"Lỗi khi chạy testcase {testcase}: {e}")
    
    print("\n============ KẾT THÚC THỰC NGHIỆM ============")
    print(f"Đã chạy {len(testcases)} testcase")
    print(f"Evaluation logs đã được lưu vào thư mục {output_dir}")

if __name__ == "__main__":
    # Định nghĩa thư mục lưu kết quả cho Kaggle
    output_dir = f'F:/LIFO tree/raw_results'


    # Khởi tạo list testcase
    testcases = []
    folder_path = f'F:/LIFO tree/data/pdp_100'
    
    # Lấy tất cả file trong thư mục
    for filename in os.listdir(folder_path):
        # Kiểm tra nếu file kết thúc bằng .txt
        if filename.endswith('.txt'):
            # Thêm vào list testcase (có hoặc không bao gồm .txt)
            testcases.append(filename[:-4])  # Giữ nguyên cả đuôi .txt
            # Hoặc: testcases.append(filename[:-4])  # Bỏ đuôi .txt
    # Chia thành 5 phần
    sp = split_list(testcases, 5)
    cd = ["lc204"]
    #print(sp[0])
    run_experiments(cd, folder_path=folder_path, output_dir=output_dir)