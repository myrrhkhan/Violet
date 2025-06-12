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


# %% [markdown]
#  ## Load model

# %%
def load_model(dotkeras_path: str):
    prediction_model = tf.keras.models.load_model(dotkeras_path)
    return prediction_model


# %% [markdown]
#  ## Image preprocess functions

# %%
AUTOTUNE = tf.data.AUTOTUNE

batch_size = 1
padding_token = 99
image_width = 128
image_height = 32
max_len = 21

# placeholder variables
characters = []
char_to_num = []
num_to_char = []

# placeholder variables
characters = []
char_to_num = []
num_to_char = []

def distortion_free_resize(image, img_size):
    w, h = img_size
    image = tf.image.resize_with_pad(image, h, w)
    # documentation had a different thing with 
    # tf.image.resize, find padding diff, then tf.pad
    # found this function instead and I guess it works fine

    # lines below convert from vertical to horizontal, then flips to correct orientation
    image = tf.transpose(image, perm=[1, 0, 2])
    image = tf.image.flip_left_right(image)
    return image

def preprocess_image(base64_img, img_size=(image_width, image_height)):
    image = tf.io.decode_image(tf.io.decode_base64(base64_img), channels=1)
    image = distortion_free_resize(image, img_size)
    image = tf.cast(image, tf.float32) / 255.0 # cast to float instead of int
    return image

def process_image_labels(base64_img, label):
    # calls above functions, gets preprocessed image and label, returns as dict
    image = preprocess_image(base64_img)
    return {"image": image, "label": label}

def prepare_dataset(base64_imgs, labels):
    # calls all functions above, makes tf dataset with image paths, 
    # maps image paths and labels to tf images and tf labels
    # TODO look up AUTOTUNE
    dataset = tf.data.Dataset.from_tensor_slices((base64_imgs, labels)).map(
        process_image_labels, num_parallel_calls=AUTOTUNE
    )
    return dataset.batch(batch_size).cache().prefetch(AUTOTUNE)


# %% [markdown]
#  ## Image prediction function(s)

# %%
# A utility function to decode the output of the network.
def decode_batch_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    # Use greedy search. For complex tasks, you can use beam search.
    results = tf.keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][
        :, :max_len
    ]
    # Iterate over the results and get back the text.
    output_text = []
    for res in results:
        res = tf.gather(res, tf.where(tf.math.not_equal(res, -1)))
        res = tf.strings.reduce_join(num_to_char(res)).numpy().decode("utf-8")
        output_text.append(res)
    return output_text


# %% [markdown]
#  ## Main function

# %%
def update_charthing(arg1_char):
    global characters
    global char_to_num
    global num_to_char
    charfile = open(arg1_char, 'r')
    characters = charfile.read()
    characters = characters.split(' ')

    # Mapping characters to integers.
    char_to_num = StringLookup(vocabulary=list(characters), mask_token=None)

    # Mapping integers back to original characters.
    num_to_char = StringLookup(
        vocabulary=char_to_num.get_vocabulary(), mask_token=None, invert=True
    )

def predict(img_base64: str, dotkeras_path: str, charpath: str) -> str:
    update_charthing(charpath)
    img_base64 = img_base64.replace('+', '-')
    img_base64 = img_base64.replace('/', '_')
    dataset = prepare_dataset([img_base64], ["null"])
    prediction_model = load_model(dotkeras_path)
    for batch in dataset:
        batch_image = batch["image"]
        pred = prediction_model.predict(batch_image)
        pred_text = decode_batch_predictions(pred)

    return pred_text

# %%
if __name__ == "__main__":
    arg1_char = sys.argv[1]
    arg2_model = sys.argv[2]
    arg3_64 = sys.argv[3]

    print(predict(arg3_64, arg2_model, arg1_char))




# %%
