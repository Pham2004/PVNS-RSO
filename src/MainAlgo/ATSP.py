from Simulator.Graph import Graph
from Simulator.Solution import Solution
import random
from Simulator.CostCalculationEvent import CostCalculator, CostCalculationEvent
from Simulator.Vehicle import Vehicle

class ATSP(object):
    def __init__(self, graph: Graph):
        self.graph = graph
        self.evaluation_count = 0
        CostCalculator.add_listener(self)
        
    def on_cost_calculated(self, event: CostCalculationEvent):
        """Implementation của CostListener interface"""
        self.evaluation_count += 1
        
    def run(self, tree, evaluation_limit):
        """
        Tối ưu hóa thứ tự các nút con cho mỗi nút trong cây.
        Phiên bản tối ưu hóa, tránh sử dụng deepcopy.
        
        Args:
            tree: Cây cần tối ưu hóa
            
        Returns:
            Tree: Cây đã được tối ưu hóa
        """
        # Lấy danh sách các nút có ít nhất 2 con
        nodes_with_children = [node for node in tree.tree_nodes.values() 
                            if len(node.children) > 1 and node.label >= 0]
        
        # Xáo trộn danh sách nút để tăng tính ngẫu nhiên
        random.shuffle(nodes_with_children)
        
        # Biến theo dõi có cải thiện hay không
        improved = False
        self.evaluation_count = 0
        
        for node in nodes_with_children:
            child_subtrees = node.children
            num_children = len(child_subtrees)
            
            if num_children <= 1:
                continue
                
            # Lưu lại chi phí hiện tại
            original_solution = Solution.tree_to_tours(tree)
            original_cost = CostCalculator.calculate(self.graph, original_solution.vehicle_list)
            
            # Lưu lại thứ tự ban đầu của các con
            original_order = list(node.children)
            
            if num_children <= 7:
                # Sử dụng duyệt hoán vị cho trường hợp số lượng con <= 7
                import itertools
                
                best_cost = original_cost
                best_order = original_order
                
                # Tạo các hoán vị và xáo trộn để tăng tính ngẫu nhiên
                permutations = list(itertools.permutations(range(num_children)))
                random.shuffle(permutations)
                
                for perm in permutations:
                    # Tạo thứ tự mới
                    new_order = [child_subtrees[i] for i in perm]
                    
                    # Lưu lại thứ tự hiện tại
                    temp_order = node.children
                    
                    # Áp dụng thứ tự mới
                    node.children = new_order
                    
                    # Kiểm tra chi phí
                    solution = Solution.tree_to_tours(tree)
                    if Solution.is_sol_feasible(self.graph, solution.vehicle_list):
                        cost = CostCalculator.calculate(self.graph, solution.vehicle_list)
                        
                        if cost < best_cost:
                            best_cost = cost
                            best_order = list(new_order)  # Tạo bản sao để lưu lại
                    
                    # Khôi phục lại thứ tự ban đầu cho node.children
                    node.children = temp_order
                    if self.evaluation_count >= evaluation_limit:
                        break
                
                # Nếu tìm thấy cải thiện, áp dụng thứ tự tốt nhất
                if best_cost < original_cost:
                    node.children = best_order
                    print(f"ATSP cải thiện chi phí từ {original_cost:.2f} xuống {best_cost:.2f} cho nút có {num_children} con")
                    
            else:
                tour_indices = []
                unvisited = set(range(num_children))
                
                depot = node
                while (depot.label != 0):
                    depot = depot.parent
                # Thuật toán regret-2
                while unvisited:
                    best_regret = -float('inf')
                    best_node_idx = None
                    best_pos = -1
                    best_cost_after_insertion = float('inf')
                    
                    # Đánh giá mỗi nút chưa được thăm
                    for node_idx in unvisited:
                        # Tính chi phí khi chèn node_idx vào mỗi vị trí trong tour
                        insertion_costs = []
                        
                        for pos in range(len(tour_indices) + 1):
                            # Tạo tour mới với node_idx được chèn vào vị trí pos
                            new_tour_indices = tour_indices.copy()
                            new_tour_indices.insert(pos, node_idx)
                            
                            # Tạo thứ tự mới dựa trên tour mới
                            new_order = [child_subtrees[idx] for idx in new_tour_indices]
                            
                            # Lưu thứ tự hiện tại
                            temp_order = node.children
                            
                            # Áp dụng thứ tự mới
                            node.children = new_order
                            
                            # Kiểm tra chi phí
                            travel_path = Solution.subtree_to_travel_path(self.graph, depot)
                            cost = Vehicle.cal_total_all_cost(self.graph, travel_path)
                            insertion_costs.append((pos, cost))
                            
                            # Khôi phục thứ tự ban đầu
                            node.children = temp_order
                        
                        # Nếu không có vị trí khả thi, bỏ qua nút này
                        if not insertion_costs:
                            continue
                        
                        # Sắp xếp theo chi phí tăng dần
                        insertion_costs.sort(key=lambda x: x[1])
                        
                        # Tính regret-2
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
                        # Không tìm thấy nút nào có thể thêm vào
                        break
                    
                    # Thêm nút tốt nhất vào tour
                    tour_indices.insert(best_pos, best_node_idx)
                    unvisited.remove(best_node_idx)
                
                # Kiểm tra xem tất cả các nút đã được thêm vào tour chưa
                if len(tour_indices) == num_children:
                    # Tạo thứ tự mới dựa trên tour_indices
                    new_order = [child_subtrees[idx] for idx in tour_indices]
                    
                    # Kiểm tra chi phí của thứ tự mới
                    node.children = new_order
                    
                    solution = Solution.tree_to_tours(tree)
                    if Solution.is_sol_feasible(self.graph, solution.vehicle_list):
                        cost = CostCalculator.calculate(self.graph, solution.vehicle_list)
                        
                        if cost < original_cost:
                            # Đã tìm thấy cải thiện
                            print(f"ATSP cải thiện chi phí từ {original_cost:.2f} xuống {cost:.2f} cho nút có {num_children} con")
                        else:
                            # Khôi phục thứ tự ban đầu nếu không cải thiện
                            node.children = original_order
                    else:
                        # Khôi phục thứ tự ban đầu nếu không khả thi
                        node.children = original_order
                else:
                    # Không tìm được tour hoàn chỉnh, giữ nguyên thứ tự ban đầu
                    node.children = original_order
                    
            if self.evaluation_count >= evaluation_limit:
                break
            
        return tree
