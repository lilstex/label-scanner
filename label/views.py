from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .models import User, Label
from .forms import MyUserCreationForm
from . import process


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
        image = request.FILES.get('image')
        if not image:
            image = request.POST.get('image')
       
        # Upload image to cloudinary
        public_url = process.upload_to_cloudinary(image)

        # Compare the images
        matching_image_url = process.find_matching_image_url(public_url, labels)
        # Extract the texts of the new label
        contents, compare = process.extract_text_from_image(public_url)

        if matching_image_url is None:
            notice = 'There is no match for this label. It has been saved successfully.'
            # Save the image url in the database
            new_object = Label.objects.create(image_url=public_url, contents=contents, compare=compare)

            if new_object is None:
                messages.error(request, 'Unable to save label')
                return render(request, 'label/upload.html')
            else:
                context = {'labels': labels, 'label_count': label_count, 'newLabel': new_object.image_url, 'contents': new_object.contents, 'notice': notice}
                return render(request, 'label/label.html', context)    
        else:
            # Get the content of the matching label
            label = Label.objects.get(image_url=matching_image_url)

            # Compare contents of the two matching labels 
            text_arr = process.compare_texts(label.compare, compare)
            
            context = {'labels': labels, 'label_count': label_count, 'disparity': text_arr, 'matchLabel': label.image_url, 'newLabel': public_url, 'contents': label.contents}

            return render(request, 'label/label.html', context)
     
    context = {'labels': labels, 'label_count': label_count}
    return render(request, 'label/label.html', context)


@login_required(login_url='login')
def capture_label(request):
    return render(request, 'label/capture.html')

@login_required(login_url='login')
def upload_label(request):
    return render(request, 'label/upload.html')

