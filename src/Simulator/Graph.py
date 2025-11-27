import numpy as np
from Simulator.Node import Node
from Simulator.Request import Request

class Graph:
    def __init__(self, file_path, cd: float, xi: float, kappa: float, p: float, A: float, mk: float, g: float, cr: float, b1: float, b2: float, p1: float, p2: float, psi: float, pi: float, R: float, eta: float, rho, Q, v):
        super()
        self.num_node, self.nodes, self.dist, self.vehicle_num, self.vehicle_capacity, self.num_request, self.requests, self.node_request_id\
            = self.creat_from_file(file_path)
        self.cd = cd
        self.p = p
        self.A = A 
        self.mk = mk
        self.g = g
        self.cr = cr
        self.b1 = b1
        self.b2 = b2
        self.p2 = p2
        self.p1 = p1
        self.xi = xi
        self.kappa = kappa
        self.psi = psi 
        self.pi = pi
        self.R = R 
        self.eta = eta
        self.rho = rho
        self.Q = Q
        self.count = np.zeros((self.num_node, self.num_node))
        self.pheromone_mat = np.ones((self.num_node, self.num_node))
        self.heuristic_info_mat = 1 / self.dist
        self.v = v
            
    def creat_from_file(self, file_path):
        node_list = []
        with open(file_path, 'rt') as f:
            count = 1
            for line in f:
                if count == 1:
                    vehicle_num, vehicle_capacity, vehicle_speed = line.split()
                    vehicle_num = int(vehicle_num)
                    vehicle_capacity = int(vehicle_capacity)
                else:
                    node_list.append(line.split())
                count += 1
        num_nodes = len(node_list)
        nodes = list(Node(int(item[0]), float(item[1]), float(item[2]), float(item[3]), float(item[4]), float(item[5]), float(item[6]), int(item[7]), int(item[8])) for item in node_list)

        dist = np.zeros((num_nodes, num_nodes))
        num_request = 0
        request_list = [Request(0,0,0)]
        node_request_id = [0] * num_nodes
        for i in range(num_nodes):
            if nodes[i].demand > 0:
                num_request += 1
                node_request_id[i] = num_request
                node_request_id[nodes[i].did] = num_request
                request_list.append(Request(num_request,nodes[i].id,nodes[i].did))
            node_a = nodes[i]
            dist[i][i] = 1e-8
            for j in range(i+1, num_nodes):
                node_b = nodes[j]
                dist[i][j] = Graph.calculate_dist(node_a, node_b)
                if (dist[i][j] < 1e-8):
                    dist[i][j] = 1e-8
                #    dist[i][j] = float('inf')
                dist[j][i] = dist[i][j]
                
        return num_nodes, nodes, dist, vehicle_num, vehicle_capacity, num_request, request_list, node_request_id

                
    @staticmethod
    def calculate_dist(node_a, node_b):
        return np.linalg.norm((node_a.x - node_b.x, node_a.y - node_b.y))
