import jwt
from accounts.models import Administrator, Customer, User
from accounts.permissions import IsAdministrator, IsCustomer
from accounts.sendMails import send_activation_mail, send_password_reset_email
from accounts.serializers import (CustomerProfileSerializer,
                                  CustomerRegistrationSerializer,
                                  LoginSerializer,
                                  ResetPasswordEmailRequestSerializer,
                                  SetNewPasswordSerializer, UserSerializer)
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.shortcuts import render
from django.utils.encoding import (DjangoUnicodeDecodeError, force_bytes,
                                   force_str, smart_bytes, smart_str)
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import serializers, status, viewsets
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)


class LoginViewSet(ModelViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    http_method_names = ["post", ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)

        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data,
                        status=status.HTTP_200_OK)


class CustomerRegistrationViewSet(ModelViewSet, TokenObtainPairView):
    serializer_class = CustomerRegistrationSerializer
    permission_classes = [AllowAny]
    http_method_names = ["post", ]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=False,
                               role="customer")
        user_data = serializer.data
        send_activation_mail(user_data, request)

        refresh = RefreshToken.for_user(user)
        res = {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
        return Response({
            "user": serializer.data,
            'refresh': res['refresh'],
            "token": res["access"]
        },
            status=status.HTTP_201_CREATED
        )


class RefreshViewSet(viewsets.ViewSet, TokenRefreshView):
    permission_classes = (AllowAny,)
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        return Response(serializer.validated_data, status=status.HTTP_200_OK)


def VerifyEmail(request):
    token = request.GET.get("token")
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms="HS256"
        )
        user = User.objects.get(id=payload['user_id'])
        if not user.is_active:
            user.is_active = True
            user.save()
            messages.success(request,
                             "Account was Successfully Verified.")
        else:
            messages.info(request,
                          """Your Account has already been activated.
                          You can now login and 
                          place your order today.
                        """)
    except jwt.ExpiredSignatureError as identifier:
        messages.warning(request,
                         "The Activation Link Expired!")
    except jwt.exceptions.DecodeError as identifier:
        messages.warning(request, "Invalid Activation Link!")
    context = {
    }
    return render(request, "accounts/verify.html", context)


# Password Reset


class RequestPasswordResetEmail(ModelViewSet):
    serializer_class = ResetPasswordEmailRequestSerializer
    permission_classes = (AllowAny,)
    http_method_names = ["post", ]

    def get_queryset(self):
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        self.get_serializer(data=request.data)
        email = request.data["email"]
        user = self.get_queryset().filter(email=email)
        if user:
            user = User.objects.get(email=email)
            if user.is_active:
                send_password_reset_email(user, request)
            return Response(
                {"Success": "We have emailed you a link to reset your password"},
                status=status.HTTP_200_OK
            )
        return Response({"Success": "Password Reset Link was sent to your email."})


def PasswordResetTokenCheck(request, uidb64, token):
    try:
        id = smart_bytes(urlsafe_base64_decode(uidb64))
        user = User.objects.get(id=id)
        if not PasswordResetTokenGenerator().check_token(user, token):
            messages.info(
                request,
                "Password Reset link is no longer valid, Please request a new one.")
    except DjangoUnicodeDecodeError as identifier:
        if not PasswordResetTokenGenerator().check_token(user, token):
            messages.info(
                request,
                "Password is no longer valid, Please request a new one.")
    context = {
        "uidb64": uidb64,
        "token": token,
    }
    return render(request, "accounts/password_reset.html", context)


class SetNewPasswordAPIView(ModelViewSet):
    serializer_class = SetNewPasswordSerializer
    permission_classes = (AllowAny,)
    http_method_names = ['post', "get"]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            password = request.data["password"]
            password_confirmation = request.data["password_confirmation"]
            token = request.data["token"]
            uidb64 = request.data["uidb64"]
            if (password and password_confirmation
                    and password != password_confirmation):
                raise serializers.ValidationError(
                    {"Error": ("Passwords don\'t match!")}
                )
            else:
                id = force_str(urlsafe_base64_decode(uidb64))
                user = User.objects.get(id=id)
                if not PasswordResetTokenGenerator().check_token(user, token):
                    raise AuthenticationFailed(
                        "The Reset Link is Invalid!",
                        401,
                    )
                else:
                    user.set_password(password)
                    user.save()
                    return Response(
                        {"success": "Password reset successful"},
                        status=status.HTTP_201_CREATED)
        except Exception as e:
            raise AuthenticationFailed(
                "The Reset Link is Invalid!", 401)
        return Response(serializer.data)
