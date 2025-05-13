import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.agent_tools import list_supported_entities, list_supported_items

print(list_supported_entities(mode="all"))
print(list_supported_entities(mode="type", search_type="assembling-machine"))
# print(list_supported_items())