# Speech & Emotion Recognition

### Follow the instruction below
- brew install python@3.13
- create venv - python3.13 -m venv srVenv313
- activate venv - source srVenv313/bin/actiavte
- python -m pip install --upgrade pip setuptools wheel
- pip install pyttsx3 "pyobjc>=9.0.1" SpeechRecognition
- pip install pyaudio
    - if ‘pyaudio’ install fails
        → brew install portaudio        
        do this first and try again
- pip install lmstudio
- lms get qwen/qwen3-4b-2507 - If it’s not accepting the install, restart VScode

### Copy/Paste below list on the terminal

```
brew install python@3.13
python3.13 -m venv srVenv313
source srVenv313/bin/actiavte
python -m pip install --upgrade pip setuptools wheel
pip install pyttsx3 "pyobjc>=9.0.1" SpeechRecognition
brew install portaudio 
pip install pyaudio
pip install lmstudio
lms get qwen/qwen3-4b-2507
```


# Run the code
1. Run the python code
2. Enter your name
3. Enter "on" to activate the record
4. Enter "respond" to get reply on the terminal