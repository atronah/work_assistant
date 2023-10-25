import os


def encrypt_credentials(name, key, username, password, force_rewrite=False):
    filename = f'{name}.crd'
    
    if os.path.isfile(filename) and not force_rewrite:
        raise Exception(f'Encrypted credentials with name "{name}" already exists')

    with open(filename, 'wb') as f:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        
        key = pad(key.encode(), 16)[:16]
        credentials = f'{username}:{password}'
        cipher = AES.new(key, AES.MODE_EAX)
        
        encrypted, tag = cipher.encrypt_and_digest(credentials.encode())
        [ f.write(x) for x in (cipher.nonce, tag, encrypted) ]
        
        return True


def decrypt_credentials(name, key):
    filename = f'{name}.crd'
    
    if not os.path.isfile(filename):
        raise Exception(f'Ecrypted credentials with name "{name}" does not exist')
    
    with open(filename, 'rb') as f:
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        
        nonce, tag, encrypted = [ f.read(x) for x in (16, 16, -1) ]
        key = pad(key.encode(), 16)[:16]
        
        cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
        decrypted = cipher.decrypt_and_verify(encrypted, tag)
        
        username, password = decrypted.decode().split(':')
        
        return username, password