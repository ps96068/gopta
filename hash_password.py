from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")




print(pwd_context.hash('qwerty'))

qwerty_hash = "$2b$12$Iga2CJFw.AYzkSdkphkCAu7eeCgPbG.Nvxhh1bcoZ1HcvJwgc0Xxq"