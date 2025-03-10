import asyncio
import time

async def classify(links):
    tasks = [process_link(link) for link in links]
    results = await asyncio.gather(*tasks)
    ans = []
    for res in results:
        if 'yes' in str(res[1]).lower():
            ans.append(res[0])
    return ans

from tensorflow.keras.preprocessing.sequence import pad_sequences
import string

def classify_url(model, url, threshold=0.5):
    """Classify a single URL using the trained character-level model."""
    # Encode the URL into character indices

    MAX_LEN = 400
    char_vocab = list(string.ascii_lowercase + string.ascii_uppercase + string.digits + "-./:")
    char_to_index = {char: i + 1 for i, char in enumerate(char_vocab)}  # +1 to reserve index 0 for padding
    char_to_index["UNK"] = len(char_to_index) + 1
    encoded_url = [char_to_index.get(c, char_to_index["UNK"]) for c in url]
    # Pad the sequence to MAX_LEN
    encoded_url = pad_sequences([encoded_url], maxlen=MAX_LEN, padding='post', truncating='post')

    prob = model.predict(encoded_url)[0][0]  # Extract the single probability score
    prediction = 1 if prob >= threshold else 0
    return prediction, prob

import tensorflow as tf
async def get_links(link):
    return [link]

async def main():
    s = time.time()
    links = await get_links("https://www.amazon.com/s?k=guitars&i=mi&crid=300DVHGXQJ6MM&sprefix=guitars%2Cmi%2C278&ref=nb_sb_noss_1")
    #ans = await classify(links)

    # Load the model from the HDF5 format

    loaded_model = tf.keras.models.load_model("Link_Classifier.h5")

    # Example of running a new URL classification
    for new_url in links:
        pred, prob = classify_url(loaded_model, new_url)
        print(new_url)
        print(f"Predicted Class: {pred} (Probability: {prob:.4f})")
        print("**")
    print(f"Total Time: {time.time()-s}")

asyncio.run(main())
