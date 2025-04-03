import subprocess
import time
import sys
import os

# Get the path to the Python interpreter for the current virtual environment
python_executable = sys.executable

# Step 0: Run embedding script
print("Running embedding.py...")
embedding_process = subprocess.Popen([python_executable, "embedding.py"])
embedding_process.wait()

# Step 1: Run FAQ generation script
print("Running faq_generation.py...")
faq_process = subprocess.Popen([python_executable, "faq_generation.py"])
faq_process.wait()

# Step 2: Run backend script (keep running)
print("Starting backend.py...")
backend_process = subprocess.Popen([python_executable, "backend.py"])

# Wait a while to make sure the backend starts successfully
time.sleep(3)

# Step 3: Run Streamlit app (still use command line tool)
print("Launching Streamlit app...")
streamlit_process = subprocess.Popen(["streamlit", "run", "main.py"])

# Optional: wait for all programmes to finish (Ctrl+C to stop)
try:
    streamlit_process.wait()
except KeyboardInterrupt:
    print("Stopping all processes...")
    backend_process.terminate()
    streamlit_process.terminate()
