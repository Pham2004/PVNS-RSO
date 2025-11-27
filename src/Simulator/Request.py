class Request(object):
    def __init__(self, rid: int, pick_up_id, delivery_id):
        """
        Khởi tạo một yêu cầu vận chuyển (pickup-delivery).
        
        Args:
            rid: ID của yêu cầu
            pick_up_id: ID của nút pickup
            delivery_id: ID của nút delivery
        """
        super()
        self.id = rid
        self.pick_up_id = pick_up_id
        self.delivery_id = delivery_id