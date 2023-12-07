import cv2
import numpy as np
import requests
import pytesseract
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import User, Label
from .forms import MyUserCreationForm
from io import BytesIO


# Custom functions

def extract_text_from_image(image_path):
    # Load image using cv2
    cv_img = load_image(image_path)

    if cv_img is not None:
        # Convert from BGR to RGB format/mode
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        text_arr = extract_text(img_rgb, cv_img)

        # Stringify the extracted texts
        text_str = '\n'.join(text_arr)

        return text_str
    else:
        print('Error processing image')
        return None


def load_image(image_path):
    response = requests.get(image_path)
    if response.status_code == 200:
        image_bytes = response.content
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        return cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    else:
        print('Error downloading image')
        return None


def extract_text(img_rgb, cv_img):
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


def download_image_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for unsuccessful HTTP responses
        image_data = BytesIO(response.content)
        return cv2.imdecode(np.frombuffer(image_data.read(), np.uint8), cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"Failed to download image from URL {url}: {e}")
        return None


def find_matching_image_url(input_image_url, labels):
    # Download the input image from the URL
    input_image = download_image_from_url(input_image_url)
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
        image_to_compare = download_image_from_url(label.image_url)
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
        good_matches = [m for m, n in matches if m.distance < 0.75 * n.distance]

        # Calculate the match percentage
        match_percentage = len(good_matches) / len(kp_input) * 100

        # Update the best match if the current image has a higher match percentage
        if match_percentage > best_match_percentage:
            best_match_percentage = match_percentage
            best_match_url = label.image_url

    # Check if the best match percentage is greater than 75
    if best_match_percentage >= 75:
        return best_match_url
    else:
        return None


def compare_contents(original, new):
    # Load image using cv2
    response = requests.get(original)
    if response.status_code == 200:
        image_bytes = response.content
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        cv_img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    else:
        print('Error downloading image')
    
    # Convert from BGR to RGB format/mode
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

    text_arr = []

    # Working with image to data
    data = pytesseract.image_to_data(img_rgb)
    for id, line in enumerate(data.splitlines()):
        if id != 0:  # Eliminating the first row
            line = line.split()
            if len(line) == 12:
                x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
                cv2.rectangle(cv_img, (x, y), (w + x, h + y), (0, 255, 0), 2)
                cv2.putText(cv_img, line[11], (x, y), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)
                text_arr.append(line[11])

    return cv_img, text_arr




# Create your views here.

def loginPage(request):
    page = 'login'
    # Redirect user to home page if they are already logged in
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
       
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Email OR Password does not exit')

    context = {'page': page}
    return render(request, 'label/login_register.html', context)


def logoutUser(request):
    logout(request)
    return redirect('home')


def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = user.email.lower()

            # Check if a user with the same email already exists
            if User.objects.filter(email=user.email).exists():
                messages.error(request, 'This email address is already in use.')
                return render(request, 'label/login_register.html', {'form': form})

            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'An error occurred during registration')

    return render(request, 'label/login_register.html', {'form': form})


def extract_contents(image_url):
    # Load image using cv2
    response = requests.get(image_url)
    if response.status_code == 200:
        image_bytes = response.content
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        cv_img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    else:
        print('Error downloading image')
    
    # Convert from BGR to RGB format/mode
    img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

    text_arr = []

    # Working with image to data
    data = pytesseract.image_to_data(img_rgb)
    for id, line in enumerate(data.splitlines()):
        if id != 0:  # Eliminating the first row
            line = line.split()
            if len(line) == 12:
                x, y, w, h = int(line[6]), int(line[7]), int(line[8]), int(line[9])
                cv2.rectangle(cv_img, (x, y), (w + x, h + y), (0, 255, 0), 2)
                cv2.putText(cv_img, line[11], (x, y), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)
                text_arr.append(line[11])

    return cv_img, text_arr



@login_required(login_url='login')
def home(request):
    # Compare label with existing labels
    labels = Label.objects.all()
    label_count = labels.count()

    context = {'labels': labels, 'label_count': label_count}
    return render(request, 'label/home.html', context)


@login_required(login_url='login')
def label(request):
    # Compare label with existing labels
    labels = Label.objects.all()
    label_count = labels.count()

    if request.method == 'POST':
        image = request.POST.get('image')
        # image = 'https://res.cloudinary.com/lilstex/image/upload/v1701866854/WhatsApp_Image_2023-11-27_at_2.43.15_PM_4_houeo1.jpg'
        # Compare the images and extract text and compare
        matching_image_url = find_matching_image_url(image, labels)

        if matching_image_url is not None:
            # Extract the texts 
            contents = extract_text_from_image(image)
            pass
            # text_arr = compare_contents(original, new)
            # diff_in_arr2 = list(set(arr2) - set(arr1))
            # match_label = label.image
            # disparity = text_arr
            # context = {'labels': labels, 'label_count': label_count, 'disparity': disparity, 'matchLabel': match_label, 'newLabel': image}

            # return render(request, 'label/home.html', context)
        else:
            # Extract the texts of the new label
            contents = extract_text_from_image(image)
            contents = contents
            notice = 'There is no match for this label. Its a new item.'
            # Save the label
            try:
                new_object = Label.objects.create(image_url=image, contents=contents)
            except:
                messages.error(request, 'Label was not saved')

            if new_object is not None:
                context = {'labels': labels, 'label_count': label_count, 'newLabel': image, 'notice': notice}
                return render(request, 'label/label.html', context)
            else:
                messages.error(request, 'Unable to save label')

            return render(request, 'label/upload.html', context)

        
    context = {'labels': labels, 'label_count': label_count}
    return render(request, 'label/label.html', context)



@login_required(login_url='login')
def capture_label(request):
    return render(request, 'label/upload.html')


# def capture_label(request):
#     if request.method == 'POST':
#         image = request.POST.get('image')
#         # Compare label with existing labels

#         # Compare the images

#         # Extract text and compare
#         contents = ['Text', 'Onions', 'Garlic']
#         try:
#             label = Label.objects.create(image=image, contents=contents)
#         except:
#             messages.error(request, 'Unable to upload a label')
        
#         if label is not None:
#             return redirect('home')
#         else:
#             messages.error(request, 'Unable to upload a label')
    
#     return render(request, 'label/capture.html')


# def label_info(request, pk):
#     room = Room.objects.get(id=pk)
#     room_messages = room.message_set.all()
#     participants = room.participants.all()

#     if request.method == 'POST':
#         message = Message.objects.create(
#             user=request.user,
#             room=room,
#             body=request.POST.get('body')
#         )
#         room.participants.add(request.user)
#         return redirect('room', pk=room.id)

#     context = {'room': room, 'room_messages': room_messages,
#                'participants': participants}
#     return render(request, 'base/room.html', context)


# def userProfile(request, pk):
#     user = User.objects.get(id=pk)
#     rooms = user.room_set.all()
#     room_messages = user.message_set.all()
#     topics = Topic.objects.all()
#     context = {'user': user, 'rooms': rooms,
#                'room_messages': room_messages, 'topics': topics}
#     return render(request, 'base/profile.html', context)


# @login_required(login_url='login')
# def delete_label(request, pk):
#     room = Room.objects.get(id=pk)

#     if request.user != room.host:
#         return HttpResponse('Your are not allowed here!!')

#     if request.method == 'POST':
#         room.delete()
#         return redirect('home')
#     return render(request, 'base/delete.html', {'obj': room})

