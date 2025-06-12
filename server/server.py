from flask import Flask, request, jsonify
import base64
import os
from predict import predict_image

app = Flask(__name__)

# Configuration - you can modify these or move to environment variables
MODEL_PATH = "model.keras"  # Update with your model path
CHAR_PATH = "characters.txt"  # Update with your characters file path

@app.route('/predict', methods=['POST'])
def predict_endpoint():
    try:
        # Get image from request
        if 'image' not in request.files and 'image_base64' not in request.json:
            return jsonify({'error': 'No image provided'}), 400
        
        # Handle file upload
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename == '':
                return jsonify({'error': 'No image selected'}), 400
            
            # Convert uploaded file to base64
            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Handle base64 image in JSON
        elif request.is_json and 'image_base64' in request.json:
            image_base64 = request.json['image_base64']
            # Remove data URL prefix if present
            if image_base64.startswith('data:image'):
                image_base64 = image_base64.split(',')[1]
        
        else:
            return jsonify({'error': 'Invalid image format'}), 400
        
        # Make prediction
        prediction = predict_image(image_base64, MODEL_PATH, CHAR_PATH)
        
        return jsonify({
            'success': True,
            'prediction': prediction
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'message': 'Image Prediction API',
        'endpoints': {
            'POST /predict': 'Upload image for prediction',
            'GET /health': 'Health check',
            'GET /': 'This message'
        }
    })

if __name__ == '__main__':
    # Check if model and character files exist
    if not os.path.exists(MODEL_PATH):
        print(f"Warning: Model file {MODEL_PATH} not found")
    if not os.path.exists(CHAR_PATH):
        print(f"Warning: Character file {CHAR_PATH} not found")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
