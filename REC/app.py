from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__)

# 連接到 MongoDB (替換為你的 MongoDB URI)
MONGO_URI = "mongodb+srv://aleee:foodproject@cluster0.gucwp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
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

@app.route('/search_dhr', methods=['GET', 'POST'])
def search_dhr():
    if request.method == 'POST':
        title = request.form.get('title')  # 獲取使用者輸入的 title
        if not title:
            return render_template('homepage.html', error="請輸入標題！")
        
        data = collection_dhr.find_one({"title": title}, {"_id": 0})  # 查詢資料
        if data:
            return render_template('homepage.html', data=data, title=title)
        else:
            return render_template('homepage.html', error="找不到該標題的資料！")
    
    return render_template('homepage.html')

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
