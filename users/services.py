import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.core.mail import send_mail


def generate_token(user):

    payload = {
        "user_id": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return token


def generate_verification_token(user):

    payload = {
        "user_id": user.id,
        "exp": datetime.utcnow() + timedelta(minutes=30)
    }

    token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

    return token


# def send_verification_email(user, token):
#     verify_link = f"http://127.0.0.1:8000/verify/{token}/"
#
#     subject = "Verify your account"
#
#     html_message = f"""
#         <h3>Hello {user.username}</h3>
#
#         <p>Click the button below to verify your account:</p>
#
#         <a href="{verify_link}"
#            style="padding:10px 20px;
#                   background:#28a745;
#                   color:white;
#                   text-decoration:none;
#                   border-radius:5px;">
#             Verify Account
#         </a>
#
#         <p>This link expires in 30 minutes.</p>
#         """
#
#     send_mail(
#         subject,
#         "",
#         "noreply@example.com",
#         [user.email],
#         html_message=html_message,
#         fail_silently=False,
#     )