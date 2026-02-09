from app.database.models.user_model import UserModel
from app.database.models.order_model import OrderModel

# автогенерейт, чтение метаданных | иначе миграция пустая
__all__ = ["UserModel", "OrderModel"]