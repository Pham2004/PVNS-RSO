from Simulator.Graph import Graph
from Simulator.Solution import Solution
import random
from Simulator.CostCalculationEvent import CostCalculator, CostCalculationEvent

class LocalSearch(object):
    def __init__(self, graph: Graph):
        self.graph = graph
        self.evaluation_count = 0
        self.evaluation_limit = 0
        CostCalculator.add_listener(self)

    def on_cost_calculated(self, event: CostCalculationEvent):
        """Implementation của CostListener interface"""
        self.evaluation_count += 1
        
    def run(self, tree, evaluation_limit):
        """
        Phiên bản tối ưu nhất của local search sử dụng Variable Neighborhood Descent (VND).
        Đã loại bỏ các kiểm tra thừa và tăng cường hiệu suất.
        
        Args:
            tree: Cây biểu diễn giải pháp cần tối ưu
            
        Returns:
            Tree: Cây đã được tối ưu hóa
        """
        if tree is None:
            return None
        
        # Tính chi phí ban đầu
        original_solution = Solution.tree_to_tours(tree)
        if not Solution.is_sol_feasible(self.graph, original_solution.vehicle_list):
            return tree  # Trả về cây ban đầu nếu không khả thi
            
        current_cost = CostCalculator.calculate(self.graph, original_solution.vehicle_list)
        initial_cost = current_cost
        
        # Danh sách các phép toán theo thứ tự tăng dần về chi phí tính toán
        operators = [
            ("node_relocate", self.try_node_relocate_optimized),
            ("subtree_relocate", self.try_subtree_relocate_optimized),
            ("node_swap", self.try_node_swap_optimized),
            ("subtree_swap", self.try_subtree_swap_optimized),
            ("rotate_to_descendant",self.try_rotate_to_descendant_optimized)
        ]
        
        # Biến lưu trữ số lần mỗi phép toán không cải thiện liên tiếp
        self.evaluation_count = 0
        self.evaluation_limit = evaluation_limit
        non_improving_counts = {op_name: 0 for op_name, _ in operators}
        max_non_improving = 3  # Sau 3 lần không cải thiện, tạm bỏ qua phép toán này
                
        operator_index = 0
        
        # Variable Neighborhood Descent: Thử tuần tự các phép toán
        while operator_index < len(operators) and self.evaluation_count < self.evaluation_limit:
            op_name, op_func = operators[operator_index]
            
            # Bỏ qua phép toán này nếu nó đã không cải thiện nhiều lần liên tiếp
            if non_improving_counts[op_name] >= max_non_improving:
                operator_index += 1
                continue
            
            #print(f"  Thử phép toán {op_name}...")
            
            try:
                # Thực hiện phép toán và lấy kết quả
                operator_improved, new_cost = op_func(tree, current_cost)
                
                if operator_improved:
                    #print(f"  ✓ {op_name} cải thiện từ {current_cost} xuống {new_cost}")
                    current_cost = new_cost
                    improved = True
                    
                    # Reset counter cho phép toán này
                    non_improving_counts[op_name] = 0
                        
                    # Bắt đầu lại từ đầu danh sách phép toán (VND)
                    operator_index = 0
                else:
                    # Phép toán không cải thiện
                    non_improving_counts[op_name] += 1
                    #print(f"  ✗ {op_name} không cải thiện ({non_improving_counts[op_name]}/{max_non_improving})")
                    
                    # Chuyển sang phép toán tiếp theo
                    operator_index += 1

                if self.evaluation_count >= self.evaluation_limit:
                    break
            
            except Exception as e:
                print(f"  Lỗi khi chạy {op_name}: {str(e)}")
                non_improving_counts[op_name] += 1
                operator_index += 1
            
        
        # In kết quả cuối cùng
        improvement = initial_cost - current_cost
        improvement_percentage = (improvement / initial_cost) * 100 if initial_cost > 0 else 0
        print(f"Chi phí ban đầu: {initial_cost}, Chi phí cuối: {current_cost}")
        print(f"Cải thiện: {improvement} ({improvement_percentage:.2f}%)")
        
        return tree

    def try_node_swap_optimized(self, tree, current_cost):
        """
        Phiên bản tối ưu của try_node_swap, giảm thiểu deepcopy.
        
        Args:
            tree: Cây biểu diễn giải pháp cần tối ưu
            current_cost: Chi phí hiện tại để so sánh
            
        Returns:
            tuple: (True/False đã cải thiện, chi phí mới nếu cải thiện)
        """
        # Tạo danh sách các nút yêu cầu
        request_nodes = [node for label, node in tree.tree_nodes.items() 
                        if isinstance(label, int) and label > 0]
        
        # Xáo trộn danh sách để tăng tính ngẫu nhiên
        random.shuffle(request_nodes)
        
        # Thử hoán đổi từng cặp nút
        for node1 in request_nodes:
            # Lọc nhanh các node còn lại phù hợp để hoán đổi
            remaining_nodes = [node for node in request_nodes if node != node1 
                            and node.parent is not None and node1.parent is not None]
            
            random.shuffle(remaining_nodes)
            
            for node2 in remaining_nodes:
                # Kiểm tra nhanh các điều kiện không khả thi
                # Kiểm tra quan hệ cha-con
                if node1.parent == node2 or node2.parent == node1:
                    continue
                    
                # Kiểm tra quan hệ tổ tiên
                ancestor_relation = False
                current = node2.parent
                while current and not ancestor_relation:
                    if current == node1:
                        ancestor_relation = True
                        break
                    current = current.parent
                    
                current = node1.parent
                while current and not ancestor_relation:
                    if current == node2:
                        ancestor_relation = True
                        break
                    current = current.parent
                    
                if ancestor_relation:
                    continue
                
                # Lưu trạng thái ban đầu
                parent1, parent2 = node1.parent, node2.parent
                idx1 = parent1.children.index(node1)
                idx2 = parent2.children.index(node2)
                children1, children2 = list(node1.children), list(node2.children)
                
                # Thực hiện hoán đổi trực tiếp
                parent1.children[idx1] = node2
                parent2.children[idx2] = node1
                node1.parent, node2.parent = parent2, parent1
                
                # Xử lý con
                node1.children.clear()
                node2.children.clear()
                
                for child in children2:
                    child.parent = node1
                    node1.children.append(child)
                    
                for child in children1:
                    child.parent = node2
                    node2.children.append(child)
                
                # Kiểm tra tính hợp lệ và cải thiện
                new_solution = Solution.tree_to_tours(tree)
                if Solution.is_sol_feasible(self.graph, new_solution.vehicle_list):
                    new_cost = CostCalculator.calculate(self.graph, new_solution.vehicle_list)
                    
                    if new_cost < current_cost:
                        return True, new_cost  # Dừng ngay khi tìm thấy cải thiện
                
                # Hoàn tác nếu không cải thiện
                parent1.children[idx1] = node1
                parent2.children[idx2] = node2
                node1.parent, node2.parent = parent1, parent2
                
                node1.children.clear()
                node2.children.clear()
                
                for child in children1:
                    child.parent = node1
                    node1.children.append(child)
                    
                for child in children2:
                    child.parent = node2
                    node2.children.append(child)
                    
                if self.evaluation_count >= self.evaluation_limit:
                    break
            
            if self.evaluation_count >= self.evaluation_limit:
                    break
                
        return False, current_cost

    def try_subtree_swap_optimized(self, tree, current_cost):
        """
        Phiên bản tối ưu của try_subtree_swap, giảm thiểu deepcopy.
        
        Args:
            tree: Cây biểu diễn giải pháp cần tối ưu
            current_cost: Chi phí hiện tại để so sánh
            
        Returns:
            tuple: (True/False đã cải thiện, chi phí mới nếu cải thiện)
        """
        # Tạo danh sách các nút yêu cầu (không phải depot hoặc root)
        request_nodes = [node for label, node in tree.tree_nodes.items() 
                        if isinstance(label, int) and label > 0]
        
        # Xáo trộn danh sách các nút để tìm kiếm ngẫu nhiên
        random.shuffle(request_nodes)
        
        for node1 in request_nodes:
            # Lọc nhanh các node còn lại phù hợp để hoán đổi
            remaining_nodes = [node for node in request_nodes if node != node1 
                            and node.parent is not None and node1.parent is not None]
            
            random.shuffle(remaining_nodes)
            
            for node2 in remaining_nodes:
                # Kiểm tra nhanh các điều kiện không khả thi
                # Kiểm tra quan hệ cha-con
                if node1.parent == node2 or node2.parent == node1:
                    continue
                    
                # Kiểm tra quan hệ tổ tiên - node2 không phải là con cháu của node1 và ngược lại
                is_descendant = False
                current = node2
                while current and current.parent and not is_descendant:
                    if current.parent == node1:
                        is_descendant = True
                        break
                    current = current.parent
                    
                current = node1
                while current and current.parent and not is_descendant:
                    if current.parent == node2:
                        is_descendant = True
                        break
                    current = current.parent
                    
                if is_descendant:
                    continue
                
                # Lưu trạng thái ban đầu
                parent1, parent2 = node1.parent, node2.parent
                idx1 = parent1.children.index(node1)
                idx2 = parent2.children.index(node2)
                
                # Thực hiện hoán đổi trực tiếp
                parent1.children[idx1] = node2
                parent2.children[idx2] = node1
                node1.parent, node2.parent = parent2, parent1
                
                # Kiểm tra tính hợp lệ và cải thiện
                new_solution = Solution.tree_to_tours(tree)
                if Solution.is_sol_feasible(self.graph, new_solution.vehicle_list):
                    new_cost = CostCalculator.calculate(self.graph, new_solution.vehicle_list)
                    if new_cost < current_cost:
                        return True, new_cost  # Dừng ngay khi tìm thấy cải thiện
                
                # Hoàn tác nếu không cải thiện
                parent1.children[idx1] = node1
                parent2.children[idx2] = node2
                node1.parent, node2.parent = parent1, parent2
                
                if self.evaluation_count >= self.evaluation_limit:
                    break
                
            if self.evaluation_count >= self.evaluation_limit:
                    break
        
        return False, current_cost

    def try_subtree_relocate_optimized(self, tree, current_cost):
        """
        Phiên bản tối ưu của try_subtree_relocate, có thể di chuyển các cây con
        đến vị trí con của các nút depot.
        
        Args:
            tree: Cây biểu diễn giải pháp cần tối ưu
            current_cost: Chi phí hiện tại để so sánh
            
        Returns:
            tuple: (True/False đã cải thiện, chi phí mới nếu cải thiện)
        """
        # Tạo danh sách các nút có thể di chuyển (nút yêu cầu)
        movable_nodes = [node for label, node in tree.tree_nodes.items() 
                        if isinstance(label, int) and label > 0 and node.parent is not None]
        
        # Xáo trộn danh sách để tìm kiếm ngẫu nhiên
        random.shuffle(movable_nodes)
        
        for node in movable_nodes:
            # Lưu trạng thái ban đầu
            old_parent = node.parent
            old_index = old_parent.children.index(node)
            
            # Tạo danh sách các nút cha tiềm năng
            potential_parents = []
            
            for label, parent in tree.tree_nodes.items():
                # Bỏ qua các trường hợp không hợp lệ
                if parent is None or parent == node or label == -1:
                    continue
                
                # Kiểm tra để tránh tạo chu trình - parent không phải là con cháu của node
                is_descendant = False
                current = parent
                while current and not is_descendant:
                    if current == node:
                        is_descendant = True
                        break
                    current = current.parent
                
                # Chỉ thêm vào danh sách nếu parent không phải là con cháu của node
                if not is_descendant:
                    potential_parents.append(parent)
            
            # Xáo trộn danh sách các nút cha tiềm năng
            random.shuffle(potential_parents)
            
            for parent in potential_parents:
                # Bỏ qua nếu parent là old_parent (không cần di chuyển)
                if parent == old_parent:
                    continue
                    
                # Thử các vị trí chèn vào
                positions = list(range(len(parent.children) + 1))
                random.shuffle(positions)
                
                for position in positions:
                    # Loại bỏ node khỏi parent cũ
                    old_parent.children.remove(node)
                    
                    # Chèn node vào parent mới
                    parent.children.insert(position, node)
                    node.parent = parent
                    
                    # Kiểm tra tính hợp lệ và cải thiện
                    new_solution = Solution.tree_to_tours(tree)
                    if Solution.is_sol_feasible(self.graph, new_solution.vehicle_list):
                        new_cost = CostCalculator.calculate(self.graph, new_solution.vehicle_list)
                        if new_cost < current_cost:
                            return True, new_cost  # Dừng ngay khi tìm thấy cải thiện
                    
                    # Hoàn tác nếu không cải thiện
                    parent.children.remove(node)
                    old_parent.children.insert(old_index, node)
                    node.parent = old_parent
                    
                    if self.evaluation_count >= self.evaluation_limit:
                        break
                
                if self.evaluation_count >= self.evaluation_limit:
                    break
            
            if self.evaluation_count >= self.evaluation_limit:
                    break
        
        return False, current_cost

    def try_node_relocate_optimized(self, tree, current_cost):
        """
        Phiên bản tối ưu và đơn giản của try_node_relocate, 
        tránh sử dụng deepcopy và chỉ lưu trữ thông tin cần thiết.
        
        Args:
            tree: Cây biểu diễn giải pháp cần tối ưu
            current_cost: Chi phí hiện tại để so sánh
            
        Returns:
            tuple: (True/False đã cải thiện, chi phí mới nếu cải thiện)
        """
        # Lấy danh sách tất cả các nút yêu cầu
        movable_nodes = [node for label, node in tree.tree_nodes.items() 
                        if isinstance(label, int) and label > 0 and node.parent is not None]
        
        # Xáo trộn danh sách để tìm kiếm ngẫu nhiên
        random.shuffle(movable_nodes)
        
        # Duyệt qua từng nút có thể di chuyển
        for node in movable_nodes:
            # Lưu thông tin node hiện tại
            old_parent = node.parent
            old_position = old_parent.children.index(node)
            old_children = list(node.children)
            
            # Tạo danh sách các nút cha tiềm năng
            potential_parents = []
            
            for label, potential_parent in tree.tree_nodes.items():
                # Bỏ qua các trường hợp không hợp lệ
                if potential_parent is None or potential_parent == node or label == -1:
                    continue
                
                # Kiểm tra để tránh tạo chu trình - potential_parent không phải là con cháu của node
                is_descendant = False
                current = potential_parent
                while current and not is_descendant:
                    if current == node:
                        is_descendant = True
                        break
                    current = current.parent
                
                # Chỉ thêm vào danh sách nếu potential_parent không phải là con cháu của node
                if not is_descendant:
                    potential_parents.append(potential_parent)
            
            # Xáo trộn danh sách để tăng tính ngẫu nhiên
            random.shuffle(potential_parents)
            
            for parent in potential_parents:
                # Thử tất cả các vị trí có thể trong parent
                positions = list(range(len(parent.children) + 1))
                random.shuffle(positions)
                
                for position in positions:
                    # Giới hạn số lượng anh/em bên phải xem xét để tối ưu thời gian
                    max_right_siblings = min(3, len(parent.children) - position if position < len(parent.children) else 0)
                    
                    # Thử từng cách di chuyển anh/em bên phải
                    for right_siblings_to_move in range(max_right_siblings + 1):
                        # Bước 1: Xóa node khỏi cha cũ và gắn các con vào vị trí của node
                        old_parent.children.remove(node)
                        old_position_current = old_position
                        
                        for child in list(node.children):
                            node.children.remove(child)
                            old_parent.children.insert(old_position_current, child)
                            child.parent = old_parent
                            old_position_current += 1
                        
                        # Bước 2: Chèn node vào vị trí mới trong parent
                        if position <= len(parent.children):
                            parent.children.insert(position, node)
                        else:
                            parent.children.append(node)
                        node.parent = parent
                        
                        # Bước 3: Di chuyển anh/em bên phải (nếu có)
                        siblings_moved = []
                        siblings_original_positions = []
                        
                        if right_siblings_to_move > 0 and position < len(parent.children) - 1:
                            # Chỉ xem xét đến position + right_siblings_to_move
                            end_pos = min(position + 1 + right_siblings_to_move, len(parent.children))
                            siblings_to_move = []
                            for i, sib in enumerate(parent.children[position+1:end_pos]):
                                siblings_to_move.append(sib)
                                siblings_original_positions.append(position + 1 + i)  # Vị trí thực tế trong parent.children
                            
                            # Lưu vị trí ban đầu và di chuyển từng anh/em
                            for sib in siblings_to_move:
                                parent.children.remove(sib)
                                node.children.append(sib)
                                sib.parent = node
                                siblings_moved.append(sib)
                        
                        # Bước 4: Đánh giá giải pháp mới
                        new_solution = Solution.tree_to_tours(tree)
                        if Solution.is_sol_feasible(self.graph, new_solution.vehicle_list):
                            new_cost = CostCalculator.calculate(self.graph, new_solution.vehicle_list)
                            
                            if new_cost < current_cost:
                                #print(f"Di chuyển nút {node.label} đến làm con của nút {parent.label} ở vị trí {position} "
                                      #f"với {len(siblings_moved)} anh em bên phải đã cải thiện chi phí từ {current_cost:.2f} xuống {new_cost:.2f}")
                                return True, new_cost
                        
                        # Bước 5: Hoàn tác nếu không cải thiện
                        # 5.1 Hoàn tác việc di chuyển anh/em bên phải
                        for i, sib in enumerate(siblings_moved):
                            node.children.remove(sib)
                            # Chèn lại vào vị trí ban đầu trong parent
                            if i < len(siblings_original_positions):
                                pos = siblings_original_positions[i]
                                if pos < len(parent.children):
                                    parent.children.insert(pos, sib)
                                else:
                                    parent.children.append(sib)
                            else:
                                # Nếu không có vị trí cụ thể, thêm vào cuối
                                parent.children.append(sib)
                            sib.parent = parent
                        
                        # 5.2 Xóa node khỏi parent mới
                        if node in parent.children:
                            parent.children.remove(node)

                        # 5.3 Đưa các con từ old_parent trở lại node
                        for child in old_children:
                            if child in old_parent.children:
                                old_parent.children.remove(child)
                            node.children.append(child)
                            child.parent = node
                        
                        # 5.4 Khôi phục node vào vị trí ban đầu trong old_parent
                        if old_position < len(old_parent.children):
                            old_parent.children.insert(old_position, node)
                        else:
                            old_parent.children.append(node)
                        node.parent = old_parent
                        
                        if self.evaluation_count >= self.evaluation_limit:
                            break
                    
                    if self.evaluation_count >= self.evaluation_limit:
                        break
                    
                if self.evaluation_count >= self.evaluation_limit:
                    break
        
        return False, current_cost
    
    def try_rotate_to_descendant_optimized(self, tree, current_cost):
        """
        Thực hiện xoay cây từ một nút đến một nút cháu chắt (descendant).
        Nút cháu chắt được đưa lên làm cha của nút gốc, các nút trung gian được sắp xếp lại.
        Kiểm tra tính khả thi và cải thiện chi phí.

        Args:
            tree: Cây biểu diễn giải pháp cần tối ưu
            current_cost: Chi phí hiện tại để so sánh

        Returns:
            tuple: (True/False đã cải thiện, chi phí mới nếu cải thiện)
        """
        # Lấy danh sách các nút yêu cầu
        request_nodes = [node for label, node in tree.tree_nodes.items()
                        if isinstance(label, int) and label > 0 and node.parent is not None]
        random.shuffle(request_nodes)

        for node in request_nodes:
            # Thu thập tất cả các nút cháu chắt
            descendants = []
            def collect_descendants(current):
                if isinstance(current.label, int) and current.label > 0:
                    descendants.append(current)
                for child in current.children:
                    collect_descendants(child)
            collect_descendants(node)

            # Loại bỏ chính nút hiện tại khỏi danh sách cháu chắt
            descendants = [d for d in descendants if d != node]
            if not descendants:
                continue

            # Chọn ngẫu nhiên một nút cháu chắt
            random.shuffle(descendants)
            descendant = descendants[0]

            # Lưu trạng thái ban đầu
            node_parent = node.parent
            node_parent_idx = node_parent.children.index(node) if node_parent else -1
            node_children = list(node.children)

            # Tìm đường đi từ nút gốc đến nút cháu chắt
            path = []
            current = descendant
            while current != node and current.parent:
                path.append(current)
                current = current.parent
            if current != node:
                continue  # Không tìm thấy đường đi hợp lệ
            path.append(node)
            path.reverse()  # Đảo ngược để đi từ nút gốc đến nút cháu chắt

            # Lưu trạng thái các nút trên đường đi
            path_states = []
            for p in path:
                path_states.append({
                    'node': p,
                    'parent': p.parent,
                    'children': list(p.children),
                    'parent_idx': p.parent.children.index(p) if p.parent else -1
                })
            # Thực hiện xoay: nút cháu chắt trở thành cha của nút gốc
            # Bước 1: Ngắt kết nối tất cả các nút trên đường đi
            node.parent.children.remove(node)
            for i in range(len(path)):
                p = path[i]
                p.children.clear()

            # Bước 2: Xây dựng lại cấu trúc
            for i in range(len(path) - 1):
                parent_node = path[i + 1]
                child_node = path[i]
                parent_node.children.append(child_node)
                child_node.parent = parent_node

            # Bước 3: Gắn nút gốc (path[-1]) vào nút cha ban đầu của nó
            if node_parent:
                node_parent.children.insert(node_parent_idx, path[-1])
                path[-1].parent = node_parent

            # Bước 4: Khôi phục các cây con không nằm trên đường đi
            for state in path_states:
                node = state['node']
                for child in state['children']:
                    if child not in path:
                        node.children.append(child)
                        child.parent = node

            # Kiểm tra tính khả thi và chi phí
            new_solution = Solution.tree_to_tours(tree)
            if Solution.is_sol_feasible(self.graph, new_solution.vehicle_list):
                new_cost = CostCalculator.calculate(self.graph, new_solution.vehicle_list)
                if new_cost < current_cost:
                    #print(f"Xoay từ nút {node.label} đến nút cháu chắt {descendant.label} cải thiện chi phí từ {current_cost:.2f} xuống {new_cost:.2f}")
                    return True, new_cost

            # Hoàn tác nếu không cải thiện
            for state in path_states:
                node = state['node']
                if node in node.parent.children:
                    node.parent.children.remove(node)
                if state['parent']:
                    if node not in state['parent'].children:
                        state['parent'].children.insert(state['parent_idx'], node)
                    node.parent = state['parent']
                else:
                    node.parent = None
                node.children.clear()
                for child in state['children']:
                    if child not in path:
                        node.children.append(child)
                        child.parent = node
                        
            if self.evaluation_count >= self.evaluation_limit:
                break

        return False, current_cost