# api/index.py
import sys, os
# add project root to path so you can import Main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# import your Flask app from Main.py
from Main import app

# alias for Vercel
# Vercel will now see `app` and mount your Flask app on /
# (no need to expose it as `application`)
