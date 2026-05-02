import hashlib

def generate_hash(data):

    sha = hashlib.sha256()

    sha.update(data)

    return sha.hexdigest()