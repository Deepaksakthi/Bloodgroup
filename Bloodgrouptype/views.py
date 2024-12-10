import base64
from django.shortcuts import render, HttpResponseRedirect, redirect
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import authenticate
import cv2
import os
import numpy as np
# Create your views here.
#displaying a home page
def home(request):
    return render(request, 'home.html')

#login page
def login(request):
    #form Authentication for login
    if(request.user.is_authenticated):
        return redirect('/')
    if(request.method == "POST"):
        un = request.POST['username']
        pw = request.POST['password']
        user = authenticate(request,username=un,password=pw)
        if(user is not None):
            return redirect('/bloodgroup')
        else:
            msg = 'Invalid username or password'
            form = AuthenticationForm()
            return render(request,'login.html',{'form':form,'msg':msg})
    else:
        form = AuthenticationForm()
        return render(request,'login.html',{'form':form})
    
#Registration Page
def registration(request):
    if(request.method == "POST"):
        form = UserCreationForm(request.POST)
        if(form.is_valid()):
            form.save()
            un = form.cleaned_data.get('username')
            pw = form.cleaned_data.get('password1')
            authenticate(username=un,password=pw)
            return redirect('/login')
        else:
            return render(request,'registration.html',{'form':form})
    else:
        form = UserCreationForm()
        return render(request,'registration.html', {'form':form})
    

#Profile page   
def bloodgroup(request):
    if(request.method == "POST"):
        if(request.FILES.get('abd')):
            # Read the uploaded image file
            img_file = request.FILES['abd']
            img_name = img_file.read()

            encode = base64.b64encode(img_name).decode('utf-8')
            img_url = f"data:image/jpg;base64,{encode}"

            # Decode the image data to a NumPy array
            nparr = np.frombuffer(img_name, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)


            # Convert the image to grayscale
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Apply Gaussian blur to reduce noise
            blurred_img = cv2.GaussianBlur(gray_img, (5, 5), 0)

            # Enhance the contrast using histogram equalization
            enhanced_img = cv2.equalizeHist(blurred_img)

            # Apply Otsu's thresholding
            var1, bin_img = cv2.threshold(enhanced_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Perform morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_OPEN, kernel)
            bin_img = cv2.morphologyEx(bin_img, cv2.MORPH_CLOSE, kernel)

            #Finding the Heigth and width of image
            height, width = bin_img.shape
            region_width = width // 3
 
            region_A = bin_img[0:region_width]   # A antigen test region
            region_B = bin_img[region_width:2*region_width]  # B antigen test region
            region_D = bin_img[2*region_width:] 
 
            # calculate the default formula for our blood group. that is agglutination
            def cal_agg(region):
                if region.size == 0 or cv2.countNonZero(region) == 0:
                        return 0
                val, binary_region = cv2.threshold(region, 0, 255, cv2.THRESH_BINARY)
                num_labels, label, stats, val = cv2.connectedComponentsWithStats(binary_region, connectivity=8)
                return num_labels - 1
           
            num_region_A = cal_agg(region_A)
            num_region_B = cal_agg(region_B)
            num_region_D = cal_agg(region_D)
 
            print(num_region_A,num_region_B,num_region_D)

            # Determine if blood type is positive or negative
            if num_region_D > 0 :
                blood_factor = "Positive"
            elif num_region_D <= 0:
                blood_factor = "Negative"
            else:
                blood_factor = "None"

            # Determine the blood group based on num_region_A and num_region_B
            if num_region_A > 5 and num_region_B <= 5:
                blood_group = "A"
            elif num_region_A <= 5 and num_region_B > 5:
                blood_group = "B"
            elif num_region_A > 5 and num_region_B > 5:
                blood_group = "AB"
            elif num_region_A <= 5 and num_region_B <= 5:
                blood_group = "O"
            else:
                blood_group = "Unknown"

            # Combine blood group and factor
            final_blood_type = blood_group + " " + blood_factor
            print(final_blood_type)


            # Encode the processed image back to base64
            var2, buffer = cv2.imencode('.jpg', bin_img)
            encoded_img = base64.b64encode(buffer).decode('utf-8')
            morp_img_url = f"data:image/jpeg;base64,{encoded_img}"

            # Return the image URL and the contour lengths to the template
            return render(request, 'bloodgroup.html', {'img_name' : img_file, 'img': img_url, 'morp_img_url': morp_img_url, 'blood_type':final_blood_type})
        else:
            return render(request, 'bloodgroup.html')
    else:
        return render(request, 'bloodgroup.html')