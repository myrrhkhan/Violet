import base64
import sys
import struct
import io
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel



def predict(img_base64) -> str:

    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
    print("12")
    img_base64 = base64.b64decode(img_base64)
    
    image = Image.open(io.BytesIO(img_base64)).convert("RGB")
    
    pixel_values = processor(image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print("returning")
    return generated_text

if __name__ == "__main__":
    img = sys.argv[1]
    print("Python arg")
    print(img)
    try:
        prediction = predict(img)
    except Exception as e:
        print("Error")
        print(e)
        sys.exit(1)
    print("Prediction:")
    print(prediction)
