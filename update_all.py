import os
import shutil
import subprocess
from utils import random_string

token = random_string();
with open("action_tokens.json", "w") as file: file.write('{"quit": "' + token + '"}')
subprocess.run(["curl", "https://0.0.0.0:443/quit?token=" + token])
os.remove("action_tokens.json")