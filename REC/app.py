from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
import logging
import json
from PIL import Image
import torch
from torchvision import transforms
import os
from flask_cors import CORS
import timm

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

# 連接到 MongoDB (替換為你的 MongoDB URI)
MONGO_URI = "mongodb+srv://aleee:foodproject@cluster0.gucwp.mongodb.net/?retryWrites=true&w=majority&ssl=true"
client = MongoClient(MONGO_URI)

# 指定資料庫和集合
db = client['sample_mflix']
collection_dhr = db['DHR']
collection_hr = db['HR']
collection_nr = db['NR']

# 首頁路由
@app.route('/')
def home():
    return render_template('homepage.html')

# 搜尋功能
@app.route('/search', methods=['GET'])
def search_recipes():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'error': 'Missing query parameter'}), 400

    try:
        results = list(collection_nr.find({"title": {"$regex": query, "$options": "i"}}, {"_id": 0, "title": 1}))
        return jsonify(results)
    except Exception as e:
        logging.error(f"Error occurred during search: {e}")
        return jsonify({'error': str(e)}), 500

# 詳細食譜顯示
@app.route('/recipe_detail', methods=['GET'])
def recipe_detail():
    title = request.args.get('title', '')
    if not title:
        return "Missing title parameter", 400

    try:
        # 從 DHR 集合中檢查 have_healthy_recipe 值
        dhr_entry = collection_dhr.find_one({"title": title}, {"_id": 0, "have_healthy_recipe": 1})
        if not dhr_entry:
            return jsonify({'error': 'Recipe not found in DHR collection'}), 404

        have_healthy_recipe = dhr_entry.get("have_healthy_recipe", 0)

        # 從 NR 集合中獲取一般食譜
        original_recipe = collection_nr.find_one({"title": title}, {"_id": 0})
        if not original_recipe:
            return jsonify({'error': 'Recipe not found in NR collection'}), 404

        # 處理 ingredients 和 directions 欄位格式
        if isinstance(original_recipe.get('ingredients'), str):
            original_recipe['ingredients'] = json.loads(original_recipe['ingredients'])
        if isinstance(original_recipe.get('directions'), str):
            original_recipe['directions'] = json.loads(original_recipe['directions'])

        response_data = {'original': original_recipe}

        # 如果 have_healthy_recipe 為 1，獲取健康版本食譜
        if have_healthy_recipe == 1:
            healthy_recipe = collection_hr.find_one({"title": title}, {"_id": 0})
            if healthy_recipe:
                if isinstance(healthy_recipe.get('ingredients'), str):
                    healthy_recipe['ingredients'] = json.loads(healthy_recipe['ingredients'])
                if isinstance(healthy_recipe.get('directions'), str):
                    healthy_recipe['directions'] = json.loads(healthy_recipe['directions'])
                response_data['healthy'] = healthy_recipe
            else:
                response_data['healthy'] = {'message': 'Healthy recipe not found'}
        else:
            response_data['healthy'] = None  # 沒有健康版本時設為 None

        return render_template('recipe_detail.html', recipe=response_data)
    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return jsonify({'error': str(e)}), 500



# 模型加載
LABELS = ['apple_pie', 'baby_back_ribs', 'baklava', 'beef_carpaccio', 'beef_tartare',
          'beet_salad', 'beignets', 'bibimbap', 'bread_pudding', 'breakfast_burrito',
          'bruschetta', 'caesar_salad', 'cannoli', 'caprese_salad', 'carrot_cake',
          'ceviche', 'cheese_plate', 'cheesecake', 'chicken_curry', 'chicken_quesadilla',
          'chicken_wings', 'chocolate_cake', 'chocolate_mousse', 'churros', 'clam_chowder',
          'club_sandwich', 'crab_cakes', 'creme_brulee', 'croque_madame', 'cup_cakes',
          'deviled_eggs', 'donuts', 'dumplings', 'edamame', 'eggs_benedict', 'escargots',
          'falafel', 'filet_mignon', 'fish_and_chips', 'foie_gras', 'french_fries',
          'french_onion_soup', 'french_toast', 'fried_calamari', 'fried_rice', 'frozen_yogurt',
          'garlic_bread', 'gnocchi', 'greek_salad', 'grilled_cheese_sandwich', 'grilled_salmon',
          'guacamole', 'gyoza', 'hamburger', 'hot_and_sour_soup', 'hot_dog', 'huevos_rancheros',
          'hummus', 'ice_cream', 'lasagna', 'lobster_bisque', 'lobster_roll_sandwich',
          'macaroni_and_cheese', 'macarons', 'miso_soup', 'mussels', 'nachos', 'omelette',
          'onion_rings', 'oysters', 'pad_thai', 'paella', 'pancakes', 'panna_cotta', 'peking_duck',
          'pho', 'pizza', 'pork_chop', 'poutine', 'prime_rib', 'pulled_pork_sandwich', 'ramen',
          'ravioli', 'red_velvet_cake', 'risotto', 'samosa', 'sashimi', 'scallops',
          'seaweed_salad', 'shrimp_and_grits', 'spaghetti_bolognese', 'spaghetti_carbonara',
          'spring_rolls', 'steak', 'strawberry_shortcake', 'sushi', 'tacos', 'takoyaki',
          'tiramisu', 'tuna_tartare', 'waffles']

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = timm.create_model('swin_base_patch4_window7_224', pretrained=False, num_classes=len(LABELS))

# 修正加載方式
state_dict = torch.load('swin_model_disb.pth', map_location=device)
if isinstance(state_dict, dict):
    state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}  # 去掉分布式訓練的前綴
    model.load_state_dict(state_dict)
else:
    raise ValueError("Loaded model is not a state_dict!")

model.to(device)
model.eval()  # 切換到推理模式
print("模型成功加載並轉移到設備")

# 圖片預處理與預測
def preprocess_image(image_path):
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image_path).convert("RGB")
    return transform(image).unsqueeze(0)

def predict_image(model, image_path, labels, device):
    try:
    # 定義圖片預處理轉換
        transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        # 加載並轉換圖片
        image = Image.open(image_path).convert("RGB")
        print(f"圖片 {image_path} 成功加載")  # 確認圖片是否成功加載
        input_tensor = transform(image).unsqueeze(0).to(device)
        print(f"圖片張量的形狀: {input_tensor.shape}")  # 確認圖片張量的形狀

        #模型預測
        model.eval()
        with torch.no_grad():
            outputs = model(input_tensor)
            predicted_class = torch.argmax(outputs, dim=1).item()
        return labels[predicted_class]
        
    except Exception as e:
        print(f"圖片處理或預測過程出現錯誤: {e}")
        raise

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    image_path = "uploaded_image.jpg"
    file.save(image_path)

    # 检查文件是否保存成功
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not saved.")
        return jsonify({'error': 'File not saved successfully'}), 500

    print(f"Image saved at {image_path}, size: {os.path.getsize(image_path)} bytes")

    try:
        # 调用预测函数
        predicted_label = predict_image(model, image_path, LABELS, device)
        print(f"Predicted label: {predicted_label}")
        return jsonify({'swin_prediction': predicted_label})
    except Exception as e:
        logging.error(f"Error during image prediction: {e}")
        return jsonify({'error': str(e)}), 500

    
    



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
