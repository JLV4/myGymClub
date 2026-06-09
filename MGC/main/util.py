import os, constants, datetime

def print_welcome_message():
    print_line()
    print("Welcome to myGymClub!")
    print_line()
    print(f"Running on http://127.0.0.1:{constants.PORT}")
    print("Press CTRL + C in the terminal to close this application")


def clear_terminal():
    # For Windows
    if os.name == 'nt':
        _ = os.system('cls')
    # For Mac and Linux (POSIX systems)
    else:
        _ = os.system('clear')

def print_line(): 
    print("*******************************")

def decript_id(encrypted_id):
    return encrypted_id

def encrypt_id(id):
    return id

def now():
    ct = datetime.datetime.now()
    return f"{ct.hour}:{ct.minute}::{ct.second}"