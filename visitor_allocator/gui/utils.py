import os
import sys
from tkinter import messagebox
#import pandas as pd

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If running in a normal Python environment, use the current working directory
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def validate_input_percent(value):
    """
    Esta función valida el texto ingesado por consola para los
    número de porcentaje. Deben estar entre 0-100.
    """
    try:
        # Try converting the input to a float
        num = int(value)
        # Check if the number is between 0 and 100
        if 0 <= num <= 100:
            return True
        else:
            messagebox.showerror("Input inválido", "Por favor ingrese un número entre 0 y 100")
            return False
    except ValueError:
        messagebox.showerror("Input Inválido", "Por favor ingrese un número")
        return False
    
def validate_input_positive(value):
    """
    Esta función valida el texto ingesado por consola para las visitas
    debe ser mayor a 0.
    """
    try:
        # Try converting the input to a float
        num = int(value)
        # Check if the number is between 0 and 100
        if num > 0:
            return True
        else:
            messagebox.showerror("Input inválido", "Por favor ingrese un número mayor a 0")
            return False
    except ValueError:
        messagebox.showerror("Input Inválido", "Por favor ingrese un número")
        return False    


def validate_input_float_range(value):
    """
    Esta función valida el texto ingesado por consola el peso
    de importancia categorica. Debe ser mayor a 1.0 y menor a 5.0
    """
    try:
        # Try converting the input to a float
        num = float(value)
        # Check if the number is between 0 and 100
        if 1.0 < num <= 5.0:
            return True
        else:
            messagebox.showerror("Input inválido", "Por favor ingrese un número mayor a 1.0 y menor a 5.0")
            return False
    except ValueError:
        messagebox.showerror("Input Inválido", "Por favor ingrese un número")
        return False
    
def validate_input_number_days(value):
    """
    Esta función valida el texto ingesado por consola el rango de dias
    Debe ser un numero y ser ayor o igual a 0 y menor igual que 4.
    """
    try:
        # Try converting the input to a float
        num = int(value)
        # Check if the number is between 0 and 100
        if 0 <= num <= 4:
            return True
        else:
            messagebox.showerror("Input inválido", "Por favor ingrese un número positivo entero menor igual a 4")
            return False
    except ValueError:
        messagebox.showerror("Input Inválido", "Por favor ingrese un número")
        return False

    
