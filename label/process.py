import cv2
import numpy as np
import requests
import pytesseract
import difflib
from io import BytesIO
import cloudinary
from cloudinary import uploader

# Custom functions

def load_image(image_path):
    response = requests.get(image_path)
    if response.status_code == 200:
        image_bytes = response.content
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    else:
        print('Error downloading image')
        return None


def extract_text_to_compare(img_rgb, cv_img):
    text_arr = []

    # Working with image to data
    data = pytesseract.image_to_data(img_rgb)
    for id, line in enumerate(data.splitlines()):
        if id != 0 and len(line.split()) == 12:  # Eliminate the first row and check length
            x, y, w, h = map(int, line.split()[6:10])
            cv2.rectangle(cv_img, (x, y), (w + x, h + y), (0, 255, 0), 2)
            cv2.putText(cv_img, line.split()[11], (x, y), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)
            text_arr.append(line.split()[11])

    return text_arr


def extract_text(img_rgb, config="--psm 6"):
    # Check if img_rgb is a valid NumPy array
    if not isinstance(img_rgb, np.ndarray):
        raise TypeError("`img_rgb` must be a NumPy array")

    # Preprocess the image for better accuracy
    try:
        img_gray = cv2.cvtColor(img_rgb, cv2.COLOR_BGR2GRAY)
    except cv2.error as e:
        print(f"Error during grayscale conversion: {e}")
        return []

    img_blur = cv2.GaussianBlur(img_gray, (5, 5), 0)
    img_thresh = cv2.threshold(img_blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Extract text using Tesseract
    try:
        text = pytesseract.image_to_string(img_thresh, config=config)
    except Exception as e:
        print(f"Error during Tesseract processing: {e}")
        return []

    lines = text.splitlines()

    # Filter empty lines and return list
    return [line for line in lines if line.strip()]


def find_matching_image_url(input_image_url, labels):
    if not labels:
        return None
    # Download the input image from the URL
    input_image = load_image(input_image_url)
    if input_image is None:
        print("Input image download failed. Exiting.")
        return

    # Resize the input image if needed
    input_image_resized = cv2.resize(input_image, (1000, 650))

    # Detect keypoints and compute descriptors for the input image
    orb = cv2.ORB_create()
    kp_input, desc_input = orb.detectAndCompute(input_image_resized, None)

    # Convert descriptors to np.float32 for FLANN
    desc_input = desc_input.astype(np.float32)

    # FLANN parameters
    FLANN_INDEX_KDTREE = 1
    index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
    search_params = dict(checks=50)  # or pass an empty dictionary

    # Initialize FLANN-based matcher
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    # Initialize variables
    best_match_percentage = 0
    best_match_url = None

    # Iterate through the array of image URLs
    for label in labels:
        # Download the image from the URL
        image_to_compare = load_image(label.image_url)
        if image_to_compare is None:
            print(f"Skipping comparison for image URL: {label.image_url}")
            continue

        # Resize the image if needed
        image_to_compare_resized = cv2.resize(image_to_compare, (1000, 650))

        # Detect keypoints and compute descriptors for the current image
        kp_compare, desc_compare = orb.detectAndCompute(image_to_compare_resized, None)

        # Convert descriptors to np.float32 for FLANN
        desc_compare = desc_compare.astype(np.float32)

        # Use FLANN-based matcher
        matches = flann.knnMatch(desc_input, desc_compare, k=2)

        # Apply the ratio test to get good matches
        good_matches = [m for m, n in matches if m.distance < 0.95 * n.distance]

        # Calculate the match percentage
        match_percentage = len(good_matches) / len(kp_input) * 100

        # Update the best match if the current image has a higher match percentage
        if match_percentage > best_match_percentage:
            best_match_percentage = match_percentage
            best_match_url = label.image_url
    print(best_match_percentage)
    # Check if the best match percentage is greater than 75
    if best_match_percentage >= .0:
        return best_match_url
    else:
        return None


def extract_text_from_image(image_path):
    # Load image using cv2
    cv_img = load_image(image_path)

    if cv_img is not None:
        # Convert from BGR to RGB format/mode
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        text_arr_to_compare = extract_text_to_compare(img_rgb, cv_img)
        text_arr = extract_text(img_rgb)

        # Stringify the extracted texts
        text_str_compare = '\n'.join(text_arr_to_compare)
        text_str = '\n'.join(text_arr)

        return text_str, text_str_compare
    else:
        print('Error processing image')
        return None


def compare_texts(text1, text2):
    """
    Compare two text strings and return the differences or missing strings.

    Parameters:
    - text1: The first text string.
    - text2: The second text string.

    Returns:
    - diff: A string representing the differences or missing strings.
    """
    differ = difflib.Differ()
    diff = list(differ.compare(text1.splitlines(), text2.splitlines()))

    # Filter lines that are different or present in the second text
    diff_lines = [line[2:] for line in diff if line.startswith('- ') or line.startswith('? ')]
    
    return '\n'.join(diff_lines)


def upload_to_cloudinary(image):
    upload_result = uploader.upload(image)
    # Access the public URL of the uploaded file
    public_url = upload_result['url']

    return public_url


def delete_from_cloudinary(image_url):
    # Extract the public ID from the image URL
    public_id = cloudinary.utils.public_id(image_url)

    try:
        # Delete the image using the public ID
        deletion_result = uploader.destroy(public_id)
        if deletion_result['result'] == 'ok':
            return True, "Image deleted successfully"
        else:
            return False, "Error deleting image"
    except Exception as e:
        return False, f"Error: {str(e)}"

# success, message = delete_from_cloudinary(image_url)
