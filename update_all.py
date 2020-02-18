import os
import shutil
import subprocess
from utils import random_string

token = random_string();
with open("action_tokens.json", "w") as file: file.write('{"quit": "' + token + '"}')
subprocess.run(["curl", "https://api.interoper.io/quit?token=" + token])
os.remove("action_tokens.json")
subprocess.run(["git", "pull", "origin", "master"])
for _ in range(2): subprocess.run(["pip", "install", "based_latex", "--upgrade"])
print("\nReady!\n\nNow run this:\nsudo nohup /home/ubuntu/anaconda3/envs/latex/bin/python based_latex_server.py 2>&1 </dev/null &\n")