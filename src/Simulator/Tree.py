from typing import List, Dict, Optional
from Simulator.TreeNode import TreeNode
from Simulator.Graph import Graph

class Tree(object):
    def __init__(self, graph: Graph):
        super()
        self.graph = graph
        self.root = TreeNode(-1)
        self.tree_nodes: Dict[int, TreeNode] = {-1: self.root} 
        self.vehicle_depots: List[TreeNode] = []

    def is_valid(self) -> bool:
        if self.root.label != -1 or len(self.root.children) != self.graph.vehicle_num:
            return False

        for depot in self.vehicle_depots:
            if depot.label != 0:
                return False

        request_labels = []
        for depot in self.vehicle_depots:
            def collect_requests(node: TreeNode) -> None:
                if node.label > 0:  # Chỉ lấy các nút yêu cầu
                    request_labels.append(node.label)
                for child in node.children:
                    collect_requests(child)
            
            collect_requests(depot)
        
        if sorted(request_labels) != list(range(1, self.graph.num_request + 1)):
            return False

        visited = set()
        def dfs(node: TreeNode, parent: Optional[TreeNode]) -> bool:
            if node in visited:
                return False
            visited.add(node)
            if node.parent != parent:
                return False
            for child in node.children:
                if not dfs(child, node):
                    return False
            return True
        
        return dfs(self.root, None) and len(visited) == len(self.tree_nodes)