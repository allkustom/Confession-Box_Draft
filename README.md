# 1. Set venv and activate
```
python3 -m venv venv
source venv/bin/activate
```

# 2. Isntall Dependencies
```
pip3 install -r requirements.txt
```



# 3. File path
Main Python code on
```
00 Final Code/final.py
```

Main Arduino code on
```
00 Final Code/arduino_final/arduino_final.ino
```

Main TouchDesigner code on
```
00 Final Code/TD/magicfish1.toe
```

# 4. Operation Order
1. Open TD project and set the audio device out with intended speaker.
2. Upload the Arduino code with a correct pin out setting(Can ignore after set it once)
3. Run 'final.py'
4. Select the serial port for the communication with Arduino
5. Input the speaker index through the Python terminal
6. Input the mic index through the Python terminal
7. Everything is ready to go