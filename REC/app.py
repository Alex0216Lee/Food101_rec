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
import requests
from pathlib import Path
from tqdm import tqdm

# logging.basicConfig(level=logging.DEBUG)

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

# url = "https://weiweihsu-my.sharepoint.com/:u:/g/personal/best_weiweihsu_onmicrosoft_com/EV14Df_TOEpGtp4z7Xh5NrAB7dqUsHUyggBk8sgk4oLgzA?download=1"

# output_file = "swin_model_disb.pth"
# try:
#     # 發送 GET 請求並下載檔案
#     response = requests.get(url, stream=True)
#     response.raise_for_status()  # 檢查請求是否成功

#     # 將內容寫入本地檔案
#     with open(output_file, "wb") as file:
#         for chunk in response.iter_content(chunk_size=8192):  # 分塊寫入檔案
#             file.write(chunk)
#     print(f"檔案已成功儲存為 {output_file}")
# except requests.exceptions.RequestException as e:
#     print(f"下載失敗: {e}")

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

    

# 圖片預處理與預測
def preprocess_image(image_path, image_size=224):
    transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    image = Image.open(image_path).convert("RGB")
    image = transform(image)
    return image.unsqueeze(0)  # 增加一個 batch 維度

def predict_image(model, image_path, labels, device):
    # 預處理圖片
    input_tensor = preprocess_image(image_path).to(device)

    # 設置模型為評估模式
    model.eval()

    with torch.no_grad():
        outputs = model(input_tensor)
        predicted_class = torch.argmax(outputs, dim=1).item()
        predicted_label = labels[predicted_class]

    return predicted_label

# 取得專案根目錄的絕對路徑
BASE_DIR = Path(__file__).resolve().parent

# 修改模型相關設定
MODEL_CONFIG = {
    'local_path': BASE_DIR / 'models' / 'swin_model_disb.pth',
    'cloud_url': "https://weiweihsu-my.sharepoint.com/:u:/g/personal/best_weiweihsu_onmicrosoft_com/EV14Df_TOEpGtp4z7Xh5NrAB7dqUsHUyggBk8sgk4oLgzA?download=1",
    'chunk_size': 8192
}

def ensure_model_exists():
    """確保模型檔案存在，如果不存在則下載"""
    model_path = Path(MODEL_CONFIG['local_path'])
    
    # 建立資料夾（如果不存在）
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not model_path.exists():
        print("模型檔案不存在，開始下載...")
        download_model()
    return str(model_path)

def download_model():
    """下載模型檔案"""
    try:
        response = requests.get(MODEL_CONFIG['cloud_url'], stream=True)
        response.raise_for_status()
        
        # 取得檔案總大小
        total_size = int(response.headers.get('content-length', 0))
        block_size = MODEL_CONFIG['chunk_size']
        
        with open(MODEL_CONFIG['local_path'], 'wb') as f:
            # 使用 tqdm 建立進度條
            with tqdm(total=total_size, unit='iB', unit_scale=True) as pbar:
                for data in response.iter_content(chunk_size=block_size):
                    size = f.write(data)
                    pbar.update(size)
                    
        print(f"模型檔案已下載至 {MODEL_CONFIG['local_path']}")
    except Exception as e:
        print(f"下載失敗: {e}")
        raise

model = None
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
def load_model():
    global model
    model_path = ensure_model_exists()
    model = timm.create_model('swin_base_patch4_window7_224', pretrained=False, num_classes=len(LABELS))
    state_dict = torch.load(model_path, map_location=device)
    state_dict = {k.replace("module.", ""): v for k, v in state_dict.items()}
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    print("模型成功加載並轉移到設備")
    
@app.before_request
def init():
    load_model()


@app.route('/upload', methods=['POST'])
def upload():
    try:
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

    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({'error': str(e)}), 500
    
    try:
        # 调用预测函数
        predicted_label = predict_image(model, image_path, LABELS, device)
        # predicted_label = 'apple_pie'
        print(f"Predicted label: {predicted_label}")
        return jsonify({'swin_prediction': predicted_label})
    except Exception as e:
        logging.error(f"Error during image prediction: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
