import os
import shutil
import subprocess
from utils import random_string

token = random_string();
with open("action_tokens.json", "w") as file: file.write('{"quit": "' + token + '"}')
subprocess.run(["curl", "https://api.interoper.io/quit?token=" + token])
os.remove("action_tokens.json")