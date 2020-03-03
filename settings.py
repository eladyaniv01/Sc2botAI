import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B_PROJECT_DIR = os.path.join(BASE_DIR, 'sc2bot_burny')
PROJECT_DIR = os.path.join(B_PROJECT_DIR, 'Sc2botAI')



sys.path.append(os.path.join(os.path.dirname(__file__), "Sc2botAI"))
