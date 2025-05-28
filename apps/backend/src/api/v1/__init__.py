from fastapi import APIRouter
from . import records  # users.py をインポート

# v1用のメインルーターを作成
api_router_v1 = APIRouter(prefix="/v1")

# records.py で定義したルーターをインクルード
api_router_v1.include_router(records.router)

# (今後、items.py などのルーターが増えたらここに追加していく)
# from . import items
# api_router_v1.include_router(items.router)
