import os
import base64
import argparse
import Crypto
import Crypto.Cipher
import Crypto.Cipher.AES
import Crypto.Random
from hashlib import pbkdf2_hmac

class EncryptionError(Exception):
    pass

class AESCipher:
    def __init__(self, password: bytes, salt: bytes):
        self.aes_salt_byte_len = 16
        self.aes_tag_byte_len = 16
        self.aes_key = pbkdf2_hmac(
            "sha256",
            password,
            salt,
            iterations=100_000,
            dklen=32
        )

    def encrypt(self, message: bytes) -> bytes:
        try:
            salt = Crypto.Random.get_random_bytes(self.aes_salt_byte_len)
            cipher_text, tag = Crypto.Cipher.AES.new(
                self.aes_key,
                Crypto.Cipher.AES.MODE_GCM,
                salt,
                mac_len=self.aes_tag_byte_len
            ).encrypt_and_digest(message)
            return salt + tag + cipher_text
        except Exception as ex:
            raise EncryptionError(ex)

    def decrypt(self, cipher_text: bytes) -> bytes:
        """
        Decrypts b16 encoded string and returns bytes.
        """
        try:
            salt = cipher_text[:self.aes_salt_byte_len]
            tag = cipher_text[self.aes_salt_byte_len:self.aes_salt_byte_len + self.aes_tag_byte_len]
            cipher_text = cipher_text[self.aes_salt_byte_len + self.aes_tag_byte_len:]
            message = Crypto.Cipher.AES.new(
                self.aes_key,
                Crypto.Cipher.AES.MODE_GCM,
                salt,
                mac_len=self.aes_tag_byte_len
            ).decrypt_and_verify(cipher_text, tag)
            return message
        except Exception as ex:
            raise EncryptionError(ex)

CIPHER = AESCipher(
    "password".encode(encoding="utf8"),
    "salt".encode(encoding="utf8"),
)

def _encrypt(cipher: AESCipher, args: argparse.Namespace):
    cipher_text = cipher.encrypt(args.message.encode(encoding="utf8"))
    print(f"cipher_text (base16 encoded): '{base64.b16encode(cipher_text).decode(encoding="utf8")}'")

def _decrypt(cipher: AESCipher, args: argparse.Namespace):
    message = cipher.decrypt(base64.b16decode(args.message)).decode(encoding="utf8")
    print(f"message: '{message}'")

if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()

    sub_parsers = arg_parser.add_subparsers(required=True)
    encrypt_parser = sub_parsers.add_parser("encrypt")
    encrypt_parser.add_argument("-p", "--password", required=True)
    encrypt_parser.add_argument("-s", "--salt",     required=True)
    encrypt_parser.add_argument("-m", "--message",  required=True)
    encrypt_parser.set_defaults(func=_encrypt)

    decrypt_parser = sub_parsers.add_parser("decrypt")
    decrypt_parser.add_argument("-p", "--password", required=True)
    decrypt_parser.add_argument("-s", "--salt",     required=True)
    decrypt_parser.add_argument("-m", "--message",  required=True)
    decrypt_parser.set_defaults(func=_decrypt)

    args = arg_parser.parse_args()
    cipher = AESCipher(args.password.encode("utf8"), args.salt.encode("utf8"))
    args.func(cipher, args)
