from rest_framework.authtoken.models import Token

from .models import User


def create_admin_user(
    email: str,
    first_name: str,
    last_name: str,
    phone_number: str = "",
    username: str | None = None,
    password: str = "TempPass123!@#",
) -> User:
    if User.objects.filter(email=email).exists() or User.objects.filter(username=username).exists():
        raise ValueError("User already exists")
    if username is None:
        username = email

    admin_user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone_number,
        role="admin",
        password=password,
        is_staff=True,
        is_superuser=True,
    )

    return admin_user


def get_or_create_auth_token(email: str) -> Token:
    try:
        user = User.objects.get(email=email)
        if user.role != "admin":
            raise ValueError("User is not admin")
        token, _ = Token.objects.get_or_create(user=user)
        return token

    except User.DoesNotExist:
        raise User.DoesNotExist("User does not exist")
