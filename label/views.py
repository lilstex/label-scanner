from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import User, Label
from .forms import MyUserCreationForm
import cv2
import numpy as np
import requests
import pytesseract


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


def home(request):
    # Fetch all labels
    labels = Label.objects.all()
    label_count = labels.count()
    
    context = {'labels': labels, 'label_count': label_count}
    return render(request, 'label/home.html')

def process_label(image_url):
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
def capture_label(request):
    if request.method == 'POST':
        # image010 = request.POST.get('image')
        image = 'https://res.cloudinary.com/lilstex/image/upload/v1701866854/WhatsApp_Image_2023-11-27_at_2.43.15_PM_4_houeo1.jpg'
        # Compare the images
        processed_image, text_arr = process_label(image)
        # Extract text and compare
        # Check if label is successfully created or retrieved
        contents = text_arr
        # Compare label with existing labels
        existing_label = Label.objects.filter(contents=contents)
        if existing_label.exists():
            label = existing_label.first()
            print('Already exist')
            print(label)
        else:
            # Create a new label if it doesn't exist
            try:
                label = Label.objects.create(image=image, contents=contents)
            except:
                messages.error(request, 'Unable to upload a label')
                return render(request, 'label/capture.html')
                
        if label is not None:
            return redirect('home')
        else:
            messages.error(request, 'Unable to upload a label')
    
    return render(request, 'label/capture.html')




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

