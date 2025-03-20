import factorio_rcon

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.sandbox.base import FactorioAPI


client = factorio_rcon.RCONClient("127.0.0.1", 8088, "lvshrd")
response = client.send_command("/c rcon.print(\"Hello, Factorio!\")")

print(f"RCON response: {response if response else 'no response'}")