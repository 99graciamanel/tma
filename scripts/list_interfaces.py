import subprocess
import re

cmd = ['ip', 'a']
call = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
regex = re.compile(r'[0-9]+: ([A-Za-z0-9\-]+):')
matches = regex.findall(call.stdout)
print(*matches, sep='\n')
