"""Befehl 27: Würfeln."""
import random

def würfel():
    """Befehl 27: Würfelt eine Zahl von 1 bis 6 und gibt sie als Satz zurück."""
    return f"Du hast eine {random.randint(1,6)} gewürfelt."


if __name__ == "__main__":
    print(würfel())
