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
        

    def fin(self, u):
            if self.par[u] == u:
                return u
            self.par[u] = self.fin(self.par[u])
            return self.par[u]
        
    def merge(self, u, v) -> bool:
        x = self.fin(u)
        y = self.fin(v)
        if (x == y):
            return False
        cur_route = self.route[x] + self.route[y]
        cur_route.append(0)
        cur_route.insert(0,0)
        if Solution.is_travel_path_feasible(self.graph, cur_route) == False:
            return False
        self.par[y] = x
        self.route[x].extend(self.route[y])
        self.route[y].clear()
        return True
        
    def calculate_regret_value(self, id, all_route: Solution):
        add_cost = []
        for vehicle_index in range(self.graph.vehicle_num):
            best = [float('inf'), -1, -1]
            for i in range(1, len(all_route.vehicle_list[vehicle_index].travel_path)):
                for j in range(i, len(all_route.vehicle_list[vehicle_index].travel_path)):
                    cur_route = copy.deepcopy(all_route.vehicle_list[vehicle_index].travel_path)
                    cur_route.insert(j, self.graph.nodes[id].did)
                    cur_route.insert(i, self.graph.nodes[id].id)
                    if Solution.is_travel_path_feasible(self.graph, cur_route) == False:
                        continue
                    cur_cost = Vehicle.cal_total_all_cost(self.graph, cur_route)
                    if (cur_cost < best[0]):
                        best[0] = cur_cost
                        best[1] = i
                        best[2] = j
                        
            if best[1] != -1:
                add_cost.append((best[0], vehicle_index, best[1], best[2]))
                add_cost = sorted(add_cost, key=lambda x: x[0], reverse=False)
                if len(add_cost) > 3:
                    add_cost.pop()
        if (len(add_cost) == 0):
            return float('inf'), -1, -1, -1
        if (len(add_cost) == 1):
            return float('inf'), add_cost[0][1], add_cost[0][2], add_cost[0][3]
        if (len(add_cost) == 2):
            return add_cost[1][0] - add_cost[0][0] + 1e9, add_cost[0][1], add_cost[0][2], add_cost[0][3]
        regret_cost = 0
        for i in range(1, len(add_cost)):
            regret_cost += add_cost[i][0] - add_cost[0][0]
        return regret_cost, add_cost[0][1], add_cost[0][2], add_cost[0][3]
    
    def init_solution1(self):
        for i in range(self.graph.num_node):
            if self.graph.nodes[i].demand > 0:
                self.route[i] = [self.graph.nodes[i].id, self.graph.nodes[i].did]
                self.par[i] = i
                self.first[i] = self.last[i] = 1
        s = []
        cnt = 0
        x = np.random.randint(self.graph.vehicle_num, self.graph.num_node)
        for i in range(self.graph.num_node):
            if self.graph.nodes[i].demand > 0:
                for j in range(self.graph.num_node):
                    if self.graph.nodes[j].demand > 0 and i != j:
                        u = self.graph.nodes[i].did
                        v = self.graph.nodes[j].id
                        s.append((self.graph.dist[u][0] + self.graph.dist[0][v] - self.graph.dist[u][v], i, j))
                        cnt += 1
                        if self.graph.num_node - cnt <= x:
                            break
                        
        s_sorted = sorted(s, key=lambda x: x[0], reverse=True)
        for x in s_sorted:
            u = x[1]
            v = x[2]
            if self.last[u] == 1 and self.first[v] == 1:
                if self.merge(u,v):
                    self.last[u] = 0
                    self.first[v] = 0
        vc = []
        for i in range(self.graph.num_node):
            if self.graph.nodes[i].demand > 0 and len(self.route[i]) > 0:
                vc.append(i)
        v_sorted = sorted(vc, key=lambda x: len(self.route[x]), reverse=True)
        remove_list = []
        init_solution = Solution(self.graph)
        vehicle_index = 0
        extra = np.random.randint(self.graph.vehicle_num // 10, self.graph.vehicle_num // 5)
        for i in range(len(v_sorted)):
            if i < len(v_sorted) - self.graph.vehicle_num + extra:
                for x in self.route[v_sorted[i]]:
                    if self.graph.nodes[x].demand > 0:
                        remove_list.append(x)
            else:
                init_solution.vehicle_list[vehicle_index].travel_path = self.route[v_sorted[i]]
                init_solution.vehicle_list[vehicle_index].travel_path.insert(0,0)
                vehicle_index += 1
        for vehicle in init_solution.vehicle_list:
            vehicle.travel_path.append(0)
            
        remove_list = sorted(remove_list, key=lambda x: self.graph.nodes[x].due_time)

        while len(remove_list) > 0:
            add_id = add_pickup = add_route = add_delivery = -1
            max_regret = 0
            for i in remove_list:
                if (self.graph.nodes[i].demand > 0):
                    regret, vehicle_id, position_pickup, position_delivery = self.calculate_regret_value(i, init_solution)
                    if (position_pickup == -1):
                        continue
                    if regret >= max_regret:
                        max_regret = regret
                        add_id = i 
                        add_route = vehicle_id
                        add_pickup = position_pickup
                        add_delivery = position_delivery
            remove_list.remove(add_id)
            init_solution.vehicle_list[add_route].travel_path.insert(add_delivery, self.graph.nodes[add_id].did)
            init_solution.vehicle_list[add_route].travel_path.insert(add_pickup, self.graph.nodes[add_id].id)
        tree = Solution.tours_to_tree(init_solution)
        return tree
    
    def init_solution2(self):
        tree = Tree(self.graph)
        available_node = []
        for i in range(self.graph.vehicle_num):
            depot = TreeNode(0)
            tree.root.add_child(depot)
            tree.vehicle_depots.append(depot)
            tree.tree_nodes[f"depot_{i}"] = depot
            available_node.append(depot)
            
        list_request = list(range(1, self.graph.num_request + 1))
        random.shuffle(list_request)
        for i in range(len(list_request)):
            new_node = TreeNode(list_request[i])
            par_node = random.choice(available_node)
            par_node.add_child(new_node)
            tree.tree_nodes[list_request[i]] = new_node
            available_node.append(new_node)
        return tree
    
    def init_solution3(self):
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
        count_method3 = self.pop_size - count_method1 - count_method2
        
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
        
        # Khởi tạo bằng phương pháp 3
        for i in range(count_method3):
            tree = self.init_solution3()
            if tree:
                self.forest.append(tree)
                print(f"Đã thêm giải pháp từ method3 #{len(self.forest)}")
                
        return self.forest


