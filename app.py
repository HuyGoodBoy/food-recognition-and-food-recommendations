from flask import Flask, request, jsonify, render_template
from ultralytics import YOLO
from PIL import Image
import io
import requests

app = Flask(__name__)
model = YOLO('model/bestfinal.pt')


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    img = Image.open(io.BytesIO(image_file.read()))
    results = model(img)
    ingredients = []
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = model.names[class_id]
            ingredients.append(class_name)

    return jsonify({'ingredients': ingredients})


@app.route('/suggest_recipes', methods=['POST'])
def suggest_recipes():
    ingredients = request.form.get('ingredients', '')

    if not ingredients:
        return jsonify({'error': 'No ingredients provided'}), 400

    ingredients_list = ingredients.split(',')
    ingredient_str = ','.join(ingredients_list)
    api_key = '90b8d45216624f0f93bfd64acd6d6f46'
    url = f'https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredient_str}&number=5&apiKey={api_key}'

    response = requests.get(url)
    if response.status_code == 200:
        recipes = response.json()
        enriched_recipes = []
        for recipe in recipes:
            recipe_id = recipe['id']
            recipe_title = recipe.get('title')
            recipe_image = recipe.get('image', 'No image available')
            nutrition_url = f'https://api.spoonacular.com/recipes/{recipe_id}/nutritionWidget.json?apiKey={api_key}'
            nutrition_response = requests.get(nutrition_url)
            calories = nutrition_response.json().get('calories', 'Unknown') if nutrition_response.status_code == 200 else 'Unknown'
            enriched_recipes.append({
                'id': recipe_id,
                'title': recipe_title,
                'calories': calories,
                'image': recipe_image
            })

        return jsonify({'recipes': enriched_recipes})
    else:
        return jsonify({'error': 'Failed to connect to Spoonacular API'}), 500


@app.route('/recipe/<recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    api_key = '90b8d45216624f0f93bfd64acd6d6f46'
    url = f'https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={api_key}'

    response = requests.get(url)
    if response.status_code == 200:
        recipe_data = response.json()
        instructions = recipe_data.get('instructions', 'Không có công thức hướng dẫn cho món này.')
        title = recipe_data.get('title', 'No title available')

        return jsonify({
            'title': title,
            'instructions': instructions
        })
    else:
        return jsonify({'error': 'Failed to retrieve recipe details'}), 500


if __name__ == '__main__':
    app.run(debug=True)
