import bcrypt
import random
import hashlib
import time

from typing import Callable


class Crypto:
    @staticmethod
    def md5(s: str = None) -> str:
        if s is None:
            s = str(time.time())
        return hashlib.md5(s.encode()).hexdigest()
    
    @staticmethod
    def random_num_str(length: int = 7) -> str:
        return ''.join(str(random.randint(0, 9)) for _ in range(length))
    
    @staticmethod
    async def unique_random_num_str(length: int, exists: Callable) -> str:
        while True:
            num_str = Crypto.random_num_str(length)
            if not await exists(num_str):
                return num_str
    
    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed_password.decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
