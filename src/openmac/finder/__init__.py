from __future__ import annotations

import pprint
from pathlib import Path

import xmltodict

xml_string = Path("finder.sdef").read_text()

# Convert the XML string to a Python dictionary
python_dict = xmltodict.parse(xml_string)

# Print the resulting dictionary (using pprint for readability)
print(python_dict)
