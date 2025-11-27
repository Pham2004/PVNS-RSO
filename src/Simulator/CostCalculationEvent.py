import time
from abc import ABC, abstractmethod

class CostCalculationEvent:
    """Event class chứa thông tin về lần tính cost"""
    def __init__(self, graph, vehicle_list, cost, timestamp):
        self.graph = graph
        self.vehicle_list = vehicle_list
        self.cost = cost
        self.timestamp = timestamp

class CostListener(ABC):
    """Interface cho các class muốn lắng nghe sự kiện tính cost"""
    @abstractmethod
    def on_cost_calculated(self, event: CostCalculationEvent):
        pass

class CostCalculator:
    """Singleton class quản lý việc tính toán cost và events"""
    _instance = None
    _listeners = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def add_listener(cls, listener: CostListener):
        """Thêm listener mới"""
        if listener not in cls._listeners:
            cls._listeners.append(listener)
    
    @classmethod
    def remove_listener(cls, listener: CostListener):
        """Xóa listener"""
        if listener in cls._listeners:
            cls._listeners.remove(listener)
    
    @classmethod
    def remove_all_listeners(cls):
        """Xóa tất cả listeners"""
        cls._listeners.clear()
    
    @classmethod
    def calculate(cls, graph, vehicle_list):
        """
        Tính toán cost và thông báo cho tất cả listeners
        """
        # Gọi phương thức gốc để tính cost
        from Simulator.Solution import Solution
        cost = Solution._original_cal_cost_of_all_vehicle(graph, vehicle_list)
        
        # Tạo event
        event = CostCalculationEvent(
            graph=graph,
            vehicle_list=vehicle_list,
            cost=cost,
            timestamp=time.time()
        )
        
        # Thông báo cho tất cả listeners
        cls._notify_listeners(event)
        
        return cost
    
    @classmethod
    def _notify_listeners(cls, event: CostCalculationEvent):
        """Thông báo đến tất cả listeners"""
        for listener in cls._listeners[:]:  # Copy list để tránh modification during iteration
            try:
                listener.on_cost_calculated(event)
            except Exception as e:
                print(f"Error notifying listener {listener}: {e}")