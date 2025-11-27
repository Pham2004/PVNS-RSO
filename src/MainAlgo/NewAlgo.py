from Simulator.Graph import Graph
from Simulator.Solution import Solution
from Simulator.Vehicle import Vehicle
from MainAlgo.Initialize import Initialize
from MainAlgo.LocalSearch import LocalSearch
from MainAlgo.Pertubation import Pertubation
from MainAlgo.ATSP import ATSP
from Simulator.CostCalculationEvent import CostCalculator, CostListener, CostCalculationEvent

import time

class NewAlgo(object):
    def __init__(self, graph: Graph, pop_size: int):
        self.graph = graph
        self.forest = []
        self.pop_size = pop_size
        
        self.evaluation_count = 0
        self.evaluation_limit = 50000
        self.evaluation_logs = []
        self.start_time = 0.0
        
        self.best_cost = float('inf')
        self.best_vehicle_list = None
        
        self.Init = Initialize(self.graph, self.pop_size)
        self.LocalSearch = LocalSearch(self.graph)
        self.Pertubation = Pertubation(self.graph)
        self.ATSP = ATSP(self.graph)
        CostCalculator.add_listener(self)
        
    def on_cost_calculated(self, event: CostCalculationEvent):
        """Implementation của CostListener interface"""
        self.evaluation_count += 1
        
        # Cập nhật best cost
        if event.cost < self.best_cost:
            self.best_cost = event.cost
            self.best_vehicle_list = event.vehicle_list
        
        # Log mỗi 100 lần evaluation
        if self.evaluation_count % 100 == 0:
            elapsed_time = time.time() - self.start_time
            log_entry = {
                'evaluation_count': self.evaluation_count,
                'elapsed_time': elapsed_time,
                'best_cost': self.best_cost,
            }
            self.evaluation_logs.append(log_entry)
            
            print(f"[Evaluation {self.evaluation_count}] "
                  f"Time: {elapsed_time:.2f}s, "
                  f"Best: {self.best_cost:.2f}")
    
    def VNS(self, forest):
        """
        Thực hiện tìm kiếm cục bộ trên một tập hợp các cây (rừng) với chiến lược First Improvement.
        
        Args:
            forest: Danh sách các cây giải pháp
            
        Returns:
            tuple: (Cây tốt nhất, Chi phí tốt nhất)
        """
        
        while True:
            # Áp dụng local search cho mỗi cây trong rừng
            before_best_cost = self.best_cost
            for k in range(len(forest)):
                forest[k] = self.LocalSearch.run(forest[k], 1000)
                if self.evaluation_count >= self.evaluation_limit:
                    break
            
            # Áp dụng ATSP cho mỗi cây trong rừng
            for k in range(len(forest)):
                forest[k] = self.ATSP.run(forest[k], 500)
                if self.evaluation_count >= self.evaluation_limit:
                    break
            
            if self.best_cost < before_best_cost:
                print(f"Đã tìm thấy giải pháp tốt hơn: {self.best_cost}")
            else:
                break

            if self.evaluation_count >= self.evaluation_limit:
                break
            
            # Tạo nhiễu cho các cây trong rừng để tiếp tục tìm kiếm
            for k in range(len(forest)):
                forest[k] = self.Pertubation.run(forest[k])
        
        return self.best_vehicle_list, self.best_cost
            
    def run(self):
        """
        Phương thức chính để chạy thuật toán tìm kiếm cục bộ biến đổi.
        Sử dụng chiến lược first improvement (tìm kiếm cải thiện đầu tiên).
        
        Returns:
            tuple: (Cây tốt nhất, Chi phí tốt nhất)
        """
        import time
        
        # Khởi tạo thời gian bắt đầu và reset các biến
        self.start_time = time.time()
        self.evaluation_count = 0
        self.evaluation_logs = []
        self.best_cost = float('inf')
        
        try:
            print("Khởi tạo các giải pháp ban đầu...")
            self.forest = self.Init.initialize_population({'method1': 0.0, 'method2': 0.0, 'method3': 1.0})

            print(f"Đã khởi tạo {len(self.forest)} giải pháp ban đầu")
            
            # Kiểm tra tính khả thi của các giải pháp ban đầu
            feasible_count = 0
            for tree in self.forest:
                sol = Solution.tree_to_tours(tree)
                if Solution.is_sol_feasible(self.graph, sol.vehicle_list):
                    feasible_count += 1
            
            print(f"Số giải pháp khả thi: {feasible_count}/{len(self.forest)}")
            
            # Thực hiện tìm kiếm cục bộ cải tiến
            print("Bắt đầu quá trình tìm kiếm cục bộ...")
            best_vehicle_list, best_cost = self.VNS(self.forest)
            
            if best_vehicle_list:
                print(f"Tìm thấy giải pháp tốt nhất với chi phí: {best_cost}")
                
                energy_cost = 0
                penalty_cost = 0
                
                for vehicle in best_vehicle_list:
                    energy_cost += Vehicle.cal_total_engine_energy_consumption(self.graph, vehicle.travel_path)
                    penalty_cost += Vehicle.cal_total_penalty(self.graph, vehicle.travel_path)
                
                print(f"Chi tiết chi phí:")
                print(f"- Chi phí năng lượng: {energy_cost}")
                print(f"- Chi phí phạt quá hạn: {penalty_cost}")
                
                # Lưu evaluation_logs vào file
                with open('evaluation_log.txt', 'w') as f:
                    f.write("Evaluation Count,Elapsed Time (s),Best Cost\n")
                    for log in self.evaluation_logs:
                        f.write(f"{log['evaluation_count']},{log['elapsed_time']:.5f},{log['best_cost']}\n")
                print("Đã lưu nhật ký đánh giá vào 'evaluation_log.txt'")
                
                return best_vehicle_list, best_cost, energy_cost, penalty_cost
            else:
                print("Không tìm thấy giải pháp khả thi!")
                return None, float('inf')
        
        finally:
            CostCalculator.remove_listener(self)