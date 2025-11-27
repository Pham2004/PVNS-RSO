from typing import List, Dict, Optional

# Định nghĩa lớp TreeNode để biểu diễn một nút trong cây MTSPPDL
class TreeNode:
    def __init__(self, label: int):
        self.label = label  # -1 cho nút gốc rỗng, 0 cho depot, 1, 2, ... cho yêu cầu
        self.children: List[TreeNode] = []  # Danh sách các nút con (có thứ tự)
        self.parent: Optional[TreeNode] = None  # Nút cha

    def add_child(self, child: 'TreeNode') -> None:
        child.parent = self
        self.children.append(child)
        
    def remove_child(self, child: 'TreeNode') -> bool:
        """
        Removes a child node from this node's children list.
        
        Args:
            child: The child node to remove.
            
        Returns:
            bool: True if the child was successfully removed, False if the child was not found.
        """
        if child in self.children:
            self.children.remove(child)
            return True
        return False

    def __repr__(self) -> str:
        return f"TreeNode({self.label})"