import sys
import os

# Ensure the desktop_pet package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.app import PetApp


def main():
    app = PetApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
