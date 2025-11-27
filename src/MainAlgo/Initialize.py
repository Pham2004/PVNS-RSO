from Simulator.Graph import Graph
from Simulator.Solution import Solution
import random
import numpy as np
import copy
from Simulator.Vehicle import Vehicle
from Simulator.Tree import Tree
from Simulator.TreeNode import TreeNode
from sklearn.cluster import KMeans

class Initialize(object):
    def __init__(self, graph: Graph, pop_size: int):
        self.graph = graph
        self.route = [[] for _ in range(graph.num_node)]
        self.first = [0] * graph.num_node
        self.last = [0] * graph.num_node
        self.par = [0] * graph.num_node
        self.pop_size = pop_size
        self.forest = []
        
    def init_solution1(self):
        # Initialize empty solution with vehicles starting and ending at depot
        init_solution = Solution(self.graph)
        for vehicle in init_solution.vehicle_list:
            vehicle.travel_path = [0, 0]  # Start and end at depot

        # Create list of all requests and shuffle randomly
        all_requests = list(range(1, self.graph.num_request + 1))
        all_requests.sort(key=lambda x: self.graph.nodes[self.graph.requests[x].pick_up_id].ready_time)

        # Process each request in shuffled order
        for request_id in all_requests:
            pickup_node = self.graph.requests[request_id].pick_up_id
            delivery_node = self.graph.requests[request_id].delivery_id
            
            best_cost_increase = float('inf')
            best_vehicle = None
            best_pickup_pos = -1
            best_delivery_pos = -1
            
            # Try to insert in each vehicle
            for vehicle_idx, vehicle in enumerate(init_solution.vehicle_list):
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
                vehicle = init_solution.vehicle_list[best_vehicle]
                vehicle.travel_path.insert(best_pickup_pos, pickup_node)
                vehicle.travel_path.insert(best_delivery_pos, delivery_node)
                
        tree = Solution.tours_to_tree(init_solution)
        return tree
    
    def init_solution2(self):
        # Initialize empty solution with vehicles starting and ending at depot
        init_solution = Solution(self.graph)
        for vehicle in init_solution.vehicle_list:
            vehicle.travel_path = [0, 0]  # Start and end at depot

        # Create list of all requests and shuffle randomly
        all_requests = list(range(1, self.graph.num_request + 1))
        random.shuffle(all_requests)

        # Process each request in shuffled order
        for request_id in all_requests:
            pickup_node = self.graph.requests[request_id].pick_up_id
            delivery_node = self.graph.requests[request_id].delivery_id
            
            best_cost_increase = float('inf')
            best_vehicle = None
            best_pickup_pos = -1
            best_delivery_pos = -1
            
            # Try to insert in each vehicle
            for vehicle_idx, vehicle in enumerate(init_solution.vehicle_list):
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
                vehicle = init_solution.vehicle_list[best_vehicle]
                vehicle.travel_path.insert(best_pickup_pos, pickup_node)
                vehicle.travel_path.insert(best_delivery_pos, delivery_node)
                
        tree = Solution.tours_to_tree(init_solution)
        return tree
    
    def initialize_population(self, scenario):
        """Khởi tạo quần thể theo kịch bản"""
        count_method1 = int(self.pop_size * scenario['method1'])
        count_method2 = int(self.pop_size * scenario['method2']) 
        
        # Khởi tạo bằng phương pháp 1
        for i in range(count_method1):
            tree = self.init_solution1()
            if tree:
                self.forest.append(tree)
                print(f"Đã thêm giải pháp từ method1 #{len(self.forest)}")
        
        # Khởi tạo bằng phương pháp 2
        for i in range(count_method2):
            tree = self.init_solution2()
            if tree:
                self.forest.append(tree)
                print(f"Đã thêm giải pháp từ method2 #{len(self.forest)}")
                
        return self.forest
