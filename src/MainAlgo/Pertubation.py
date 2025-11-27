from Simulator.Graph import Graph
from Simulator.Solution import Solution
from Simulator.Vehicle import Vehicle
import random
import numpy as np
import copy
from Simulator.TreeNode import TreeNode

class Pertubation(object):
    def __init__(self, graph: Graph):
        self.graph = graph
    
    def run(self, tree):
        """
        Thực hiện phép nhiễu (perturbation) để đa dạng hóa không gian tìm kiếm.
        Phương pháp này loại bỏ một cây con có chi phí lớn nhất và phân phối lại các nút của nó
        vào các vị trí tốt nhất có thể.
        
        Args:
            tree: Cây biểu diễn giải pháp cần thực hiện nhiễu
            
        Returns:
            Tree: Cây sau khi thực hiện nhiễu
        """
        current_solution = Solution.tree_to_tours(tree)
        ma = 0
        id = -1
        for vehicle_idx, vehicle in enumerate(current_solution.vehicle_list):
            cost = Vehicle.cal_total_all_cost(self.graph, vehicle.travel_path)
            if id == -1 or cost > ma:
                ma = cost
                id = vehicle_idx
        
        removed_requests = []
        for node in current_solution.vehicle_list[id].travel_path:
            if self.graph.nodes[node].demand > 0:
                removed_requests.append(node)
        current_solution.vehicle_list[id].travel_path = [0, 0]
        
        for pickup_node in removed_requests:
            delivery_node = self.graph.nodes[pickup_node].did
            
            best_cost_increase = float('inf')
            best_vehicle = None
            best_pickup_pos = -1
            best_delivery_pos = -1
            
            # Try to insert in each vehicle
            for vehicle_idx, vehicle in enumerate(current_solution.vehicle_list):
                current_route = vehicle.travel_path
                
                # Try all possible pickup positions (after depot, before delivery)
                for pickup_pos in range(1, len(current_route)):
                    # Try all possible delivery positions (after pickup position)
                    for delivery_pos in range(pickup_pos + 1, len(current_route) + 1):
                        # Create new route with inserted nodes
                        new_route = current_route.copy()
                        new_route.insert(pickup_pos, pickup_node)
                        new_route.insert(delivery_pos, delivery_node)
                        
                        # Check feasibility
                        if Solution.is_travel_path_feasible(self.graph, new_route):
                            # Calculate cost increase
                            old_cost = Vehicle.cal_total_all_cost(self.graph, current_route)
                            new_cost = Vehicle.cal_total_all_cost(self.graph, new_route)
                            cost_increase = new_cost - old_cost
                            
                            if cost_increase < best_cost_increase:
                                best_cost_increase = cost_increase
                                best_vehicle = vehicle_idx
                                best_pickup_pos = pickup_pos
                                best_delivery_pos = delivery_pos
            
            # Insert at best found position
            if best_vehicle is not None:
                vehicle = current_solution.vehicle_list[best_vehicle]
                vehicle.travel_path.insert(best_pickup_pos, pickup_node)
                vehicle.travel_path.insert(best_delivery_pos, delivery_node)
            
        print(Solution.is_sol_feasible(self.graph, current_solution.vehicle_list))
        tree_copy = Solution.tours_to_tree(current_solution)
        return tree_copy
