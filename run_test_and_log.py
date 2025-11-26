import subprocess
import sys

with open("test_output.txt", "w") as f:
    subprocess.run([sys.executable, "tests/test_live.py"], stdout=f, stderr=subprocess.STDOUT)
