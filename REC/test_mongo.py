from pymongo import MongoClient

MONGO_URI = "mongodb+srv://aleee:foodproject@cluster0.gucwp.mongodb.net/?retryWrites=true&w=majority&ssl=true"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
    print("MongoDB 連線成功！")
except Exception as e:
    print(f"MongoDB 連線失敗: {e}")
