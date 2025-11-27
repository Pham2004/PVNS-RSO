from Simulator.Graph import Graph
from Simulator.Vehicle import Vehicle
from Simulator.Tree import Tree
from Simulator.TreeNode import TreeNode
from typing import List, Dict, Optional


class Solution(object):
    def __init__(self, graph: Graph):
        super()
        self.graph = graph
        self.vehicle_list = [Vehicle(graph) for i in range(graph.vehicle_num)]
        
    @staticmethod
    def _original_cal_cost_of_all_vehicle(graph, vehicle_list):
        cost = 0
        for vehicle in vehicle_list:
            cost += Vehicle.cal_total_all_cost(graph, vehicle.travel_path)
        return cost
    
    
    @staticmethod
    def cal_cost_of_all_vehicle(graph: Graph, vehicle_list):
        from Simulator.CostCalculationEvent import CostCalculator
        return CostCalculator.calculate(graph, vehicle_list)
    
    @staticmethod
    def is_sol_sub_feasible(graph: Graph, vehicle_list):
        for vehicle in vehicle_list:
            if Solution.is_travel_path_feasible(graph, vehicle.travel_path) == False:
                return False
        return True
    
    @staticmethod
    def is_sol_feasible(graph: Graph, vehicle_list):
        num_visit = 0
        for vehicle in vehicle_list:
            num_visit += len(vehicle.travel_path) - 2
            if Solution.is_travel_path_feasible(graph, vehicle.travel_path) == False:
                return False
        if (num_visit != graph.num_node - 1):
            return False
        return True
    
    @staticmethod
    def is_travel_path_feasible(graph: Graph, travel_path):
        """
        Kiểm tra tính khả thi của một lộ trình bằng cách xác minh ràng buộc:
        - Dung lượng (capacity)
        - Thứ tự pickup-delivery (LIFO)
        
        Không kiểm tra ràng buộc time window vì đó là ràng buộc mềm.
        
        Args:
            graph: Đồ thị chứa dữ liệu bài toán
            travel_path: Lộ trình cần kiểm tra
            
        Returns:
            bool: True nếu lộ trình khả thi, False nếu không
        """
        capacity = 0  # Tải hiện tại
        current_delivery = []  # Stack cho thứ tự giao hàng (LIFO)
        
        for index, current_index in enumerate(travel_path):
            # Kiểm tra thứ tự pickup-delivery
            if current_index != 0:  # Không phải depot
                if graph.nodes[current_index].demand > 0:  # Pickup
                    current_delivery.append(current_index)
                else:  # Delivery
                    # Kiểm tra nếu delivery này tương ứng với pickup gần nhất (LIFO)
                    if not current_delivery or graph.nodes[current_index].pid != current_delivery[-1]:
                        return False  # Vi phạm ràng buộc LIFO
                    current_delivery.pop()
                
            # Kiểm tra ràng buộc dung lượng
            capacity += graph.nodes[current_index].demand
            if capacity > graph.vehicle_capacity:
                return False  # Vi phạm ràng buộc dung lượng
                
        # Đảm bảo tất cả pickup đã được delivery
        if current_delivery:
            return False  # Một số pickup chưa được delivery
            
        return True
    
    @staticmethod
    def tours_to_tree(solution) -> Tree:
        tree = Tree(solution.graph)
        cur_node = tree.root
        for vehicle_index, vehicle in enumerate(solution.vehicle_list):
            for idx, current_index in enumerate(vehicle.travel_path):
                if (solution.graph.nodes[current_index].pid == 0 and idx != len(vehicle.travel_path) - 1):
                    next_node = TreeNode(solution.graph.node_request_id[current_index])
                    cur_node.add_child(next_node)
                    cur_node = next_node
                    if solution.graph.node_request_id[current_index] == 0:
                        tree.tree_nodes[f"depot_{vehicle_index}"] = cur_node
                        tree.vehicle_depots.append(cur_node)
                    else:
                        tree.tree_nodes[solution.graph.node_request_id[current_index]] = cur_node
                else:
                    cur_node = cur_node.parent
        return tree
    
    @staticmethod
    def tree_to_tours(tree: Tree):
        tours = Solution(tree.graph)
        
        def dfs(node: TreeNode, tour: List[int]) -> None:
            tour.append(tree.graph.requests[node.label].pick_up_id) 
            for child in node.children:
                dfs(child, tour)
            tour.append(tree.graph.requests[node.label].delivery_id)
                
        for vehicle_index, depot in enumerate(tree.vehicle_depots):
            tour = []
            dfs(depot, tour)
            vehicle = Vehicle(tree.graph)
            vehicle.travel_path = tour
            tours.vehicle_list[vehicle_index].travel_path = tour
        
        return tours
    
    @staticmethod
    def subtree_to_travel_path(graph: Graph, node: TreeNode):
        travel_path = []
        def dfs(node: TreeNode, travel_path: List[int]) -> None:
            travel_path.append(graph.requests[node.label].pick_up_id)
            for child in node.children:
                dfs(child, travel_path)
            travel_path.append(graph.requests[node.label].delivery_id)
        
        travel_path = []
        dfs(node, travel_path)
        
        return travel_path
    
    