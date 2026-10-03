import os
import requests
import time

DATA_DIR = "data/images"
os.makedirs(DATA_DIR, exist_ok=True)

print("Downloading 50 random open-source images from Picsum...")
for i in range(1, 51):
    url = f"https://picsum.photos/seed/{i}/600/400"
    filepath = os.path.join(DATA_DIR, f"image_{i}.jpg")
    print(f"Downloading {filepath}...")
    try:
        img_data = requests.get(url, timeout=10).content
        with open(filepath, "wb") as f:
            f.write(img_data)
        time.sleep(0.1)
    except Exception as e:
        print(f"Failed on image {i}: {e}")

# Copy the first image to test_image.jpg for the Phase 2 test script
test_img = os.path.join(DATA_DIR, "test_image.jpg")
first_img = os.path.join(DATA_DIR, "image_1.jpg")
if os.path.exists(first_img):
    with open(first_img, "rb") as f_in:
        with open(test_img, "wb") as f_out:
            f_out.write(f_in.read())

print("\nDownload complete! You now have a solid 50-image dataset.")
