from flask import Flask, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# 連接到 MongoDB (替換為你的 MongoDB URI)
MONGO_URI = "mongodb+srv://aleee:foodproject@cluster0.gucwp.mongodb.net/sample_mflix?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)

# 指定資料庫和集合
db = client['sample_mflix']
collection_dhr = db['DHR']
collection_hr = db['HR']
collection_nr = db['NR']

@app.route('/')
def home():
    return "Welcome to the Flask-MongoDB App!"

# 添加到 DHR 集合的路由
@app.route('/add_dhr', methods=['POST'])
def add_to_dhr():
    data = request.json
    result = collection_dhr.insert_one(data)
    return jsonify({"message": "Data inserted to DHR", "id": str(result.inserted_id)})

# 從 DHR 集合獲取資料
@app.route('/get_dhr', methods=['GET'])
def get_dhr():
    data = list(collection_dhr.find({}, {"_id": 0}))
    return jsonify(data)

# 添加到 HR 集合的路由
@app.route('/add_hr', methods=['POST'])
def add_to_hr():
    data = request.json
    result = collection_hr.insert_one(data)
    return jsonify({"message": "Data inserted to HR", "id": str(result.inserted_id)})

# 從 HR 集合獲取資料
@app.route('/get_hr', methods=['GET'])
def get_hr():
    data = list(collection_hr.find({}, {"_id": 0}))
    return jsonify(data)

# 添加到 NR 集合的路由
@app.route('/add_nr', methods=['POST'])
def add_to_nr():
    data = request.json
    result = collection_nr.insert_one(data)
    return jsonify({"message": "Data inserted to NR", "id": str(result.inserted_id)})

# 從 NR 集合獲取資料
@app.route('/get_nr', methods=['GET'])
def get_nr():
    data = list(collection_nr.find({}, {"_id": 0}))
    return jsonify(data)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
