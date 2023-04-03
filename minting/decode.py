from cryptography.fernet import Fernet
import base64, msgpack

# Define the dictionary to be encrypted
my_dict = {"name": "Habibi wallahi", "description": "This is an NFT created using Algorand", "image": "tinyurl.com/3ezsyafs"}

# Generate a 32-byte encryption key
key = Fernet.generate_key()

# Create a Fernet object with the key
f = Fernet(key)

# Convert the dictionary to bytes using messagepack and encrypt it
encrypted = f.encrypt(msgpack.packb(my_dict, use_bin_type=True))

# Encode the encrypted bytes as a 32-byte string using base64
encoded = base64.urlsafe_b64encode(encrypted).decode()[:32]

print(encoded)

encrypted_bytes = base64.urlsafe_b64decode(encoded + "=" * ((4 - len(encoded) % 4) % 4))

print(encrypted_bytes)


import base64

# Assume my_bytes contains the encoded dictionary

# Decode base64 to get the original string
metadata_hash_str = "cSPfATIUYDtG0K76VT5dWxOzY8mhE/7bNkNwr7FeLBo="
metadata_hash_bytes = base64.urlsafe_b64decode(metadata_hash_str + "=" * ((4 - len(metadata_hash_str) % 4) % 4))

print(metadata_hash_bytes)


