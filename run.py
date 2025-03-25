#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, "src"))

# Import the main module and start the application
from src.main import main

if __name__ == "__main__":
    main()