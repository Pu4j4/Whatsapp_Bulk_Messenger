from django .http import JsonResponse
from .forms import RegisterForm
from django.views.decorators.csrf import csrf_exempt
from .models import User
from .services import generate_token
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from .services import generate_verification_token
import jwt
from django.conf import settings
from .decorators import login_required
from .models import Campaign
import json
import csv
import os
import openpyxl
import io
from .models import Document, Contact



@csrf_exempt
def register(request):

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(user.password)
            user.is_active = False
            user.save()

            token = generate_verification_token(user)

            verify_link = f"http://127.0.0.1:8000/verify/{token}/"

            print("\n====== EMAIL VERIFICATION LINK ======")
            print(verify_link)
            print("=====================================\n")

            return JsonResponse({
                "message": "User registered successfully. Check email for verification."
            })
        else:
            return JsonResponse({
                "message": "error",
                "errors" : form.errors
            }, status=400)
    else:
        return JsonResponse({
            "message": "Only POST method allowed"
        }, status=405)



@csrf_exempt
def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)

        except User.DoesNotExist:
            return JsonResponse({
                "error": "User not found"
            }, status=404)

        if not check_password(password, user.password):
            return JsonResponse({
                "error": "Invalid password"
            }, status=401)

        if not user.is_active:
            return JsonResponse({
                "error": "Account not verified"
            }, status=403)

        token = generate_token(user)

        return JsonResponse({
            "message": "Login successful",
            "token": token
        })

    return JsonResponse({
        "error": "POST method required"
    }, status=405)




def verify_user(request, token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

        user_id = payload.get("user_id")

        user = User.objects.get(id=user_id)

        # FIRST check if user exists
        if not user:
            return JsonResponse({
                "error": "User not found"
            }, status=404)

        # THEN check if already verified
        if user.is_active:
            return JsonResponse({
                "message": "Account already verified"
            })

        user.is_active = True
        user.save()

        return JsonResponse({
            "message": "Account verified successfully"
        })

    except jwt.ExpiredSignatureError:
        return JsonResponse({
            "error": "Verification link expired"
        }, status=400)

    except jwt.InvalidTokenError:
        return JsonResponse({
            "error": "Invalid token"
        }, status=400)




@login_required
def dashboard(request):

    return JsonResponse({
        "message": f"Welcome {request.user.username}"
    })


@csrf_exempt
@login_required
def create_campaign(request):

    if request.method == "POST":

        data = json.loads(request.body)

        campaign_name = data.get("campaign_name")
        message_text = data.get("message_text")

        campaign = Campaign.objects.create(
            user_id=request.user.id,
            campaign_name=campaign_name,
            message_text=message_text
        )

        return JsonResponse({
            "message": "Campaign created successfully",
            "campaign_id": campaign.id
        })

    return JsonResponse({"error": "POST required"}, status=405)



@csrf_exempt
@login_required
def upload_contacts(request):

    if request.method == "POST":

        file = request.FILES.get("file")

        if not file:
            return JsonResponse({"error": "No file uploaded"}, status=400)

        file_name = file.name

        document = Document.objects.create(
            user=request.user,
            file_name=file_name,
            file_path="",
            file_type="csv",
            processed_status="processing"
        )

        decoded_file = file.read().decode("utf-8")
        io_string = io.StringIO(decoded_file)

        reader = csv.DictReader(io_string)

        count = 0

        for row in reader:
            print(row)
            Contact.objects.create(
                user=request.user,
                document=document,
                name=row.get("name"),
                phone=row.get("phone"),
                email=row.get("email"),
                address=row.get("address"),
                extra_data=row
            )

            count += 1

        document.processed_status = "completed"
        document.save()

        return JsonResponse({
            "message": "Contacts uploaded successfully",
            "contacts_created": count
        })

    return JsonResponse({"error": "POST required"})