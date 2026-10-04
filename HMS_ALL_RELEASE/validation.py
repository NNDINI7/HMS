"""
validation.py
Simple input validation for CityCare Hospital.

Use these functions while taking input from the user.
"""

import re


def valid_id(value, prefix):
    """Check IDs such as P001, D001, N001."""
    value = value.strip().upper()
    pattern = rf"^{prefix}\d{{3}}$"
    return bool(re.match(pattern, value))


def get_id(prompt, prefix):
    """Keep asking until a valid ID is entered."""
    while True:
        value = input(f"{prompt} (e.g. {prefix}001): ").strip().upper()

        if valid_id(value, prefix):
            return value

        print(f"Invalid ID. Enter it like {prefix}001.")


def valid_name(name):
    """Allow letters, spaces and dots."""
    name = name.strip()

    if not name:
        return False

    return bool(re.match(r"^[A-Za-z .]+$", name))


def get_name(prompt="Name"):
    """Keep asking until a valid name is entered."""
    while True:
        name = input(
            f"{prompt} (e.g. Meera Rao): "
        ).strip()

        if valid_name(name):
            return name

        print("Invalid name. Use letters and spaces only.")


def valid_phone(phone):
    """Check a 10-digit Indian mobile number."""
    phone = phone.strip()

    return bool(
        re.match(r"^[6-9]\d{9}$", phone)
    )


def get_phone():
    """Keep asking until a valid phone number is entered."""
    while True:
        phone = input(
            "Phone (10 digits, e.g. 9876543210): "
        ).strip()

        if valid_phone(phone):
            return phone

        print(
            "Invalid phone. Enter a 10-digit number "
            "starting with 6, 7, 8 or 9."
        )


def get_age():
    """Get age between 0 and 120."""
    while True:
        try:
            age = int(
                input("Age (0-120): ")
            )

            if 0 <= age <= 120:
                return age

            print("Age must be between 0 and 120.")

        except ValueError:
            print("Enter age as a number.")


def get_positive_number(prompt):
    """Get a positive number."""
    while True:
        try:
            value = float(input(prompt))

            if value > 0:
                return value

            print("Value must be greater than 0.")

        except ValueError:
            print("Enter a valid number.")


def get_choice(prompt, choices):
    """Get one value from a fixed list."""
    choices = [str(x).upper() for x in choices]

    while True:
        value = input(
            f"{prompt} ({'/'.join(choices)}): "
        ).strip().upper()

        if value in choices:
            return value

        print(
            "Invalid choice. "
            f"Choose from: {', '.join(choices)}"
        )
