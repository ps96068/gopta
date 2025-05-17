from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

from fastapi import HTTPException, status


from database import cfg_token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = cfg_token()['secret_key']
ALGORITHM = cfg_token()['algorithm']
ACCESS_TOKEN_EXPIRE_MINUTES = cfg_token()['access_token_expire_minutes']


def verify_user_password(password, hashed_password):
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None


def check_validity_token(payload: dict):
    print("check_validity_token(payload: dict)")
    expire = payload.get('exp')

    if expire is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token supplied"
        )
    if datetime.now() > datetime.fromtimestamp(expire):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token expired!"
        )
    else:
        return True


