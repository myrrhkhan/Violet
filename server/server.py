from flask import Flask, request, jsonify
from flask_cors import CORS
from predict import predict_image
from PIL import Image
import io

app = Flask(__name__)
CORS(app)

@app.route('/predict', methods=['POST'])
def predict_endpoint():
    try:
        print(f"Content-Type received: '{request.content_type}'")
        print(f"Content-Type starts with 'image/': {request.content_type.startswith('image/')}")
        print(f"Data length: {len(request.data) if request.data else 0}")
        # Get image from request
        if request.content_type.startswith('image/'):
            image_data = request.data
            if not image_data:
                return jsonify({'error': 'Empty image data'}), 400
            image = Image.open(io.BytesIO(image_data)).convert("RGB")

        else:
            return jsonify({'error': 'No valid image provided'}), 400        
        # Make prediction
        prediction = predict_image(image)
        
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
    app.run(debug=True, host='0.0.0.0', port=8711)
