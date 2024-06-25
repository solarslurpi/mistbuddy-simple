import os
import sys


from dotenv import load_dotenv
load_dotenv()

# Print each directory in the sys.path list
print("sys.path:")
for path in sys.path:
    print(path)
# Print the PYTHONPATH environment variable
print("PYTHONPATH:")
print(os.environ.get('PYTHONPATH', 'PYTHONPATH not set'))
