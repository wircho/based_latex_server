import os
import shutil
import subprocess
from utils import random_string

token = random_string();
with open("action_tokens.json", "w") as file: file.write('{"quit": "' + token + '"}')
subprocess.run(["curl", "https://api.interoper.io/quit?token=" + token])
os.remove("action_tokens.json")
subprocess.run(["git", "pull", "origin", "master"])
should_clear_all = None
while should_clear_all != "y" and should_clear_all != "n": should_clear_all = input("Clear all (y/n)? ")
if should_clear_all == "y": subprocess.run(["python", "clear_all.py"])
for _ in range(2): subprocess.run(["pip", "install", "based_latex", "--upgrade"])
print("\nReady!\n\nNow run this:\nsudo nohup /home/ubuntu/anaconda3/envs/latex/bin/python based_latex_server.py 2>&1 </dev/null &\n")