import sys
import io
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

def predict(img_base64, dotkeras_path: str, charpath: str) -> str:
    # Image.open(io.BytesIO(img_base64))

    processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
    model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")

    img_base64 = img_base64.replace('+', '-')
    img_base64 = img_base64.replace('/', '_')
    img_base64 = bytes(img_base64, encoding='utf8')
    image = Image.open(io.BytesIO(img_base64))
    pixel_values = processor(image, return_tensors="pt").pixel_values
    generated_ids = model.generate(pixel_values)
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print(generated_text)
    return generated_text

if __name__ == "__main__":
    arg1_char = sys.argv[1]
    arg2_model = sys.argv[2]
    arg3_64 = sys.argv[3]

    print(predict(arg3_64, arg2_model, arg1_char))
