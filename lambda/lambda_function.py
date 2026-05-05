import json
import base64
import io
import os

from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from PIL import Image

MODEL_ID = "microsoft/trocr-base-handwritten"
HF_CACHE_DIR = "/tmp/huggingface"
processor = None
model = None


def get_model():
    global processor, model
    if processor is None or model is None:
        os.environ.setdefault("HF_HOME", HF_CACHE_DIR)
        os.environ.setdefault("TRANSFORMERS_CACHE", HF_CACHE_DIR)
        processor = TrOCRProcessor.from_pretrained(MODEL_ID, cache_dir=HF_CACHE_DIR)
        model = VisionEncoderDecoderModel.from_pretrained(MODEL_ID, cache_dir=HF_CACHE_DIR)
    return processor, model


def predict_image(image: Image.Image) -> str:
    processor, model = get_model()
    pixel_values = processor(image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return generated_text


def lambda_handler(event, context):
    # Handle OPTIONS preflight request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST, OPTIONS'
            },
            'body': ''
        }
    
    try:
        # Check if body exists and is base64 encoded
        if not event.get('body'):
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'No image data provided'})
            }
        
        if event.get('isBase64Encoded'):
            image_bytes = base64.b64decode(event['body'])
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        else:
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({'error': 'Image must be base64 encoded'})
            }
        
        # Run OCR prediction
        prediction = predict_image(image)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'prediction': prediction
            })
        }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e)
            })
        }
