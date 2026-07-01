#!/bin/bash
echo "Building Founder Frameworks AI App..."

# We need to make sure pyinstaller is installed in the venv
source venv/bin/activate

# Build the executable
# We add data files that need to be packaged
pyinstaller --name "FounderAI" \
            --windowed \
            --noconfirm \
            --add-data "FounderFrameworks.txt:." \
            --hidden-import="langchain" \
            --hidden-import="chromadb" \
            --hidden-import="llama_cpp" \
            app.py

echo "Build complete! Check the 'dist' folder."
