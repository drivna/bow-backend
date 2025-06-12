import bcrypt as bcrypt
import string
import random
import hashlib


class StringUtils:
    # Function to calculate SHA-256 hash of a string
    @classmethod
    def calculate_sha256_hash_first_ten(cls, input_string: str, length: int = 10) -> str:
        # Create a new SHA-256 hash object
        sha256_hash = hashlib.sha256()

        # Update the hash object with the input string
        sha256_hash.update(input_string.encode("utf-8"))

        # Get the hexadecimal representation of the hash
        hashed_string: str = sha256_hash.hexdigest()

        return hashed_string[0:length]

    @classmethod
    def hash_string(cls, data: str) -> bytes:
        # Generate a random salt
        salt: bytes = bcrypt.gensalt()

        # Concatenate the password with the salt and hash
        hashed_password: bytes = bcrypt.hashpw(data.encode("utf-8"), salt)

        return hashed_password

    @classmethod
    def check_string_against_hash(cls, data: str, hashed_data: bytes) -> bool:
        bytes_data: bytes = data.encode("utf-8")

        return bcrypt.checkpw(bytes_data, hashed_data)

    @classmethod
    def generate_random_string(cls, length: int) -> str:
        # Define the characters to choose from
        characters = (
            string.ascii_letters + string.digits
        )  # You can customize this based on your requirements

        # Use random.choice to randomly select characters and join them into a string
        random_string = "".join(random.choice(characters) for _ in range(length))

        return random_string

    @classmethod
    def to_camel_case(cls, snake_str: str) -> str:
        # Split the string into words using underscores
        components = snake_str.split("_")
        # Capitalize first letter of each component except the first one
        return components[0] + "".join(x.title() for x in components[1:])
