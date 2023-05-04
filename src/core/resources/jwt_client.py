from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken


class User:
    id = None
    softexp = None


class JWTClient(User):
    jwt_secret = settings.SECRET_KEY
    algorithm = settings.SIMPLE_JWT["ALGORITHM"]
    user = User()

    @classmethod
    def sign(cls, user_id, key=None, is_admin=None, business_id=None):

        cls.user.id = user_id
        cls.user.softexp = timedelta(minutes=50)
        refresh = RefreshToken.for_user(cls.user)
        refresh["key"] = key

        if business_id:
            refresh["business_id"] = business_id

        access_token = refresh.access_token
        access_token.set_exp(lifetime=timedelta(minutes=120))
        if is_admin:
            access_token.set_exp(lifetime=timedelta(minutes=50))

        payload = {
            "access_token": str(access_token),
        }

        return payload

    @classmethod
    def authenticate(cls, headers, is_agent=None):
        try:
            token = headers.get("Authorization").split(" ")[1]
            decoded_token = jwt.decode(
                token, cls.jwt_secret, algorithms=[cls.algorithm]
            )
            if is_agent:
                return decoded_token
            return decoded_token["user_id"]
        except Exception as e:
            print(e)
            return None

    @classmethod
    def admin_auth(cls, headers):
        new_token = jwt.encode()

    @classmethod
    def get_token(cls, headers):
        try:
            token = headers.get("Authorization")
            return token
        except Exception as e:
            print(e)
            return None

    @classmethod
    def is_token_about_to_expire(cls, token):
        try:
            token = token.split(" ")[1]
            decoded_token = jwt.decode(
                token, cls.jwt_secret, algorithms=[cls.algorithm]
            )
            expired_in = datetime.fromtimestamp(decoded_token["exp"]) - timedelta(
                minutes=10
            )
            return expired_in.minute
        except Exception as e:
            print(e)
            return None
