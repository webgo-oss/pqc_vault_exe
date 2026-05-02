from argon2 import PasswordHasher

ph = PasswordHasher()

def hash_password(password):
    return ph.hash(password)

def verify_password(hash_value, password):
    try:
        ph.verify(hash_value, password)
        return True
    except:
        return False