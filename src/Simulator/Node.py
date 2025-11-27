class Node(object):
    def __init__(self, nid: int, x: float, y: float, demand: float, ready_time: float, due_time: float, service_time: float, pid: int, did: int):
        """
        Khởi tạo một nút trong đồ thị bài toán PDPTW.
        
        Args:
            nid: ID của nút
            x: Tọa độ x
            y: Tọa độ y
            demand: Nhu cầu hàng hóa (dương: pickup, âm: delivery)
            ready_time: Thời gian bắt đầu cửa sổ thời gian
            due_time: Thời gian kết thúc cửa sổ thời gian
            service_time: Thời gian phục vụ tại nút
            pid: ID của nút pickup tương ứng (nếu là nút delivery)
            did: ID của nút delivery tương ứng (nếu là nút pickup)
        """
        super()
        self.id = nid
        self.x = x
        self.y = y
        self.demand = demand
        self.ready_time = ready_time
        self.due_time = due_time
        self.service_time = service_time
        self.pid = pid  # ID của nút pickup tương ứng
        self.did = did  # ID của nút delivery tương ứng