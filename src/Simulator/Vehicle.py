from Simulator.Graph import Graph

class Vehicle(object):
    def __init__(self, graph: Graph):
        super()
        self.current_index = 0
        self.vehicle_load = 0
        self.vehicle_time_travel = 0
        self.travel_path = [0]
        self.graph = graph
        self.current_delivery = []
            
    @staticmethod
    def cal_total_engine_energy_consumption(graph: Graph, travel_path):
        engine_energy_consumption = 0
        vehicle_load = 0
        current_ind = travel_path[0]
        for next_ind in travel_path[1:]:
            T = 1/2 * graph.cd * graph.p * graph.A * graph.v ** 3 + (graph.mk + vehicle_load) * graph.g * graph.cr * graph.v
            G = graph.xi / (graph.kappa * graph.psi) * (graph.pi * graph.R + T / graph.eta)
            engine_energy_consumption += G * graph.dist[current_ind][next_ind]
            vehicle_load += graph.nodes[next_ind].demand
            current_ind = next_ind
        return graph.p1 * engine_energy_consumption
    
    @staticmethod
    def cal_total_penalty(graph: Graph, travel_path):
        """
        Tính toán tổng thời gian quá hạn so với time window.
        Chỉ tính phạt khi đến muộn, không tính phí thời gian chờ.
        Thời gian service được tính sau khi kiểm tra time window.
        
        Args:
            graph: Đồ thị chứa dữ liệu bài toán
            travel_path: Tuyến đường cần kiểm tra
            
        Returns:
            float: Tổng chi phí phạt do quá hạn
        """
        penalty = 0
        current_time = 0  # Thời gian bắt đầu từ 0
        
        if len(travel_path) <= 1:
            return 0
        
        current_ind = travel_path[0]
        
        for next_ind in travel_path[1:]:
            # Thời gian di chuyển đến nút tiếp theo
            travel_time = graph.dist[current_ind][next_ind] / graph.v * 60
            
            # Thời điểm đến nút tiếp theo
            arrival_time = current_time + travel_time
            
            # Kiểm tra quá hạn dựa trên thời điểm đến, TRƯỚC khi tính service time
            # So sánh thời điểm đến với due_time để xác định mức độ quá hạn
            if arrival_time > graph.nodes[next_ind].due_time:
                lateness = arrival_time - graph.nodes[next_ind].due_time
                penalty += lateness
            
            # Thời gian chờ (nếu đến sớm hơn ready_time)
            wait_time = max(0, graph.nodes[next_ind].ready_time - arrival_time)
            
            # Cập nhật thời gian hiện tại: arrival_time + wait_time + service_time
            # Service time chỉ được thêm vào sau khi đã kiểm tra quá hạn và tính thời gian chờ
            current_time = arrival_time + wait_time + graph.nodes[next_ind].service_time
            
            current_ind = next_ind
        
        return graph.p2 * penalty  # Áp dụng hệ số phạt p2
    
    @staticmethod
    def cal_total_all_cost(graph: Graph, travel_path):
        """
        Tính tổng chi phí bao gồm:
        - Chi phí năng lượng tiêu thụ
        - Chi phí phạt do quá hạn
        
        Args:
            graph: Đồ thị chứa dữ liệu bài toán
            travel_path: Tuyến đường cần tính chi phí
            
        Returns:
            float: Tổng chi phí
        """
        # Chi phí năng lượng
        engine_energy_consumption = Vehicle.cal_total_engine_energy_consumption(graph, travel_path)
        
        # Chi phí phạt do quá hạn
        penalty = Vehicle.cal_total_penalty(graph, travel_path)
        
        return engine_energy_consumption + penalty