# %% [markdown]
#  # Prediction Script
#  Contains function that takes image and makes prediction from model.

# %% [markdown]
#  ## Imports

# %%
from flask import Flask
from tensorflow.keras.layers import StringLookup
import tensorflow as tf
import numpy as np
import sys
from abc import ABC, abstractmethod


# %% [markdown]
#  ## Abstract Base Classes for Future Flexibility

# %%
class ModelLoader(ABC):
    """Abstract base class for model loading"""
    
    @abstractmethod
    def load_model(self, model_path: str):
        pass

class ImagePreprocessor(ABC):
    """Abstract base class for image preprocessing"""
    
    @abstractmethod
    def preprocess_image(self, image_data: str) -> any:
        pass

class PredictionDecoder(ABC):
    """Abstract base class for prediction decoding"""
    
    @abstractmethod
    def decode_predictions(self, predictions: any) -> str:
        pass


# %% [markdown]
#  ## TensorFlow Implementation Classes

# %%
class TensorFlowModelLoader(ModelLoader):
    def load_model(self, model_path: str):
        return tf.keras.models.load_model(model_path)

class TensorFlowImagePreprocessor(ImagePreprocessor):
    def __init__(self, image_width=128, image_height=32):
        self.image_width = image_width
        self.image_height = image_height
        
    def distortion_free_resize(self, image, img_size):
        w, h = img_size
        image = tf.image.resize_with_pad(image, h, w)
        # lines below convert from vertical to horizontal, then flips to correct orientation
        image = tf.transpose(image, perm=[1, 0, 2])
        image = tf.image.flip_left_right(image)
        return image

    def preprocess_image(self, base64_img):
        image = tf.io.decode_image(tf.io.decode_base64(base64_img), channels=1)
        image = self.distortion_free_resize(image, (self.image_width, self.image_height))
        image = tf.cast(image, tf.float32) / 255.0
        return image

class TensorFlowPredictionDecoder(PredictionDecoder):
    def __init__(self, char_path: str, max_len=21):
        self.max_len = max_len
        self.characters = []
        self.char_to_num = None
        self.num_to_char = None
        self._load_characters(char_path)
    
    def _load_characters(self, char_path: str):
        with open(char_path, 'r') as charfile:
            characters_str = charfile.read()
            self.characters = characters_str.split(' ')
        
        # Mapping characters to integers
        self.char_to_num = StringLookup(vocabulary=list(self.characters), mask_token=None)
        
        # Mapping integers back to original characters
        self.num_to_char = StringLookup(
            vocabulary=self.char_to_num.get_vocabulary(), mask_token=None, invert=True
        )
    
    def decode_predictions(self, pred):
        input_len = np.ones(pred.shape[0]) * pred.shape[1]
        # Use greedy search. For complex tasks, you can use beam search.
        results = tf.keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][
            :, :self.max_len
        ]
        # Iterate over the results and get back the text.
        output_text = []
        for res in results:
            res = tf.gather(res, tf.where(tf.math.not_equal(res, -1)))
            res = tf.strings.reduce_join(self.num_to_char(res)).numpy().decode("utf-8")
            output_text.append(res)
        return output_text[0] if output_text else ""


# %% [markdown]
#  ## Prediction Pipeline Class

# %%
class PredictionPipeline:
    """Main prediction pipeline that orchestrates the components"""
    
    def __init__(self, model_loader: ModelLoader, 
                 preprocessor: ImagePreprocessor, 
                 decoder: PredictionDecoder):
        self.model_loader = model_loader
        self.preprocessor = preprocessor
        self.decoder = decoder
        self.model = None
    
    def load_model(self, model_path: str):
        self.model = self.model_loader.load_model(model_path)
    
    def predict(self, image_base64: str) -> str:
        if self.model is None:
            raise ValueError("Model not loaded. Call load_model() first.")
        
        # Clean base64 string
        image_base64 = image_base64.replace('+', '-').replace('/', '_')
        
        # Preprocess image
        processed_image = self.preprocessor.preprocess_image(image_base64)
        
        # Add batch dimension if needed
        if len(processed_image.shape) == 3:
            processed_image = tf.expand_dims(processed_image, 0)
        
        # Make prediction
        predictions = self.model.predict(processed_image)
        
        # Decode predictions
        result = self.decoder.decode_predictions(predictions)
        
        return result


# %% [markdown]
#  ## Main Prediction Function (Flask Interface)

# %%
def predict_image(image_base64: str, model_path: str, char_path: str) -> str:
    """
    Main prediction function that can be called from Flask or other interfaces.
    This function creates the pipeline and makes a prediction.
    """
    # Create components - easily swappable for different implementations
    model_loader = TensorFlowModelLoader()
    preprocessor = TensorFlowImagePreprocessor()
    decoder = TensorFlowPredictionDecoder(char_path)
    
    # Create pipeline
    pipeline = PredictionPipeline(model_loader, preprocessor, decoder)
    
    # Load model and predict
    pipeline.load_model(model_path)
    result = pipeline.predict(image_base64)
    
    return result


# %% [markdown]
#  ## Legacy Function (for backward compatibility)

# %%
def predict(img_base64: str, dotkeras_path: str, charpath: str) -> str:
    """Legacy function for backward compatibility"""
    return predict_image(img_base64, dotkeras_path, charpath)


# %% [markdown]
#  ## Command Line Interface

# %%
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python predict.py <char_file> <model_file> <base64_image>")
        sys.exit(1)
    
    arg1_char = sys.argv[1]
    arg2_model = sys.argv[2]
    arg3_64 = sys.argv[3]

    result = predict_image(arg3_64, arg2_model, arg1_char)
    print(result)
