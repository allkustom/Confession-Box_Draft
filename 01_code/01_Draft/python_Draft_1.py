import threading as th
import speech_recognition as sr
import pyttsx3
import subprocess
import json
import lmstudio as lms
import serial
import serial.tools.list_ports
import time
import random
import queue

baudrate = 115200
ports = serial.tools.list_ports.comports()
portList = []

for i in ports:
    portList.append(str(i))
    print(str(i))

com = input("Select Arduino Port: ").strip()
use = None
for i in range(len(portList)):
    if portList[i].startswith("/dev/cu.usbserial-" + str(com)):
        use = "/dev/cu.usbserial-" + str(com)
        print(f"Using {use} port")
        break

if use == None:
    print("Port not found")
    exit()

ser = serial.Serial(use, baudrate, timeout=0.1)
time.sleep(1)


lms_model = lms.llm("qwen/qwen3-4b-2507")

mic_list = sr.Microphone.list_microphone_names()
print("Mic List: ")
for i, name in enumerate(mic_list):
    print(f"[{i}] {name}")
mic_index = int(input("Select Mic Index: ").strip())


running = True
waiting = True 
doorClosed = False
userSit = False
listening = False

# TTS function
# engine = pyttsx3.init()
# engine.say("Hello World")
# engine.runAndWait()


engine = pyttsx3.init()
last_text = ""
# emotion_prompt_1 = "Tell me a single word that describe the emotion of what I said. Based on the following emotion list"
emotion_prompt_1 = "Choose one emtion from the following emotion list based on what I just said. (Answer with just the selected emotion in one word)"
emotion_list = "happy / sad / fear / disgust / surprise / anger"



print("--------------")
print("--------------")
print("--------------")
print("START")



recognizer = sr.Recognizer()
# Energy Threadhold
# Lower -> detect small sound
# Higher -> detect loud sound + good at remove noise
recognizer.energy_threshold = 150
# dynamic_energy_threshold
# Enabling auto adjustment
recognizer.dynamic_energy_threshold = True
# dynamic_energy_adjustment_ratio
# Detect sound when the sound is 1.5 times louder than the energy threshold
recognizer.dynamic_energy_adjustment_ratio = 1.5
# Pause Threshold
# Silence time between words and detect the speech is done
# Loewr -> cut the words really fast
# Higher -> cut the words slowly
recognizer.pause_threshold = 1.5
recognizer.non_speaking_duration = 0.8 
recognizer.phrase_threshold = 0.3
noise_duration = 0.8
# rate = engine.getProperty('rate')
# print (rate)
# engine.setProperty('rate', 125)  

# voices = engine.getProperty('voices')
# engine.setProperty('voice', voices[0].id) 
tts_queue = queue.Queue()


speech_data = {
    "user": 0,
    "speech": ""
}
file_name = "speech_data.json"

# speech_data["user"] = input("Enter user name: ")




print("----- CMD list -----")
# print("'on' - start recording")
# print("'off' - stop recording")
# print("'speak' - voice based on the recorded speech")
# print("'save' - save the speech data as JSON")
print("'exit' - quit code")


def seq_reset():
    global listening, last_text, waiting, doorClosed, userSit
    listening = False
    last_text= ""
    waiting = True
    doorClosed = False
    userSit = False

def seq_start_trigger(case):
    global waiting, doorClosed, userSit
    
    if case == "door":
        doorClosed = True
        print("door closed")
    elif case == "sit":
        userSit = True
        print("user sit")
    
    if doorClosed and userSit:
        waiting = False
        print("Seq start")
    else:
        waiting = True
        
    


def sr_toggle():
    global listening
    listening = not listening
    if listening:
        print("-----------------------")
        print("Confession Record Start")
        print("-----------------------")
    else:
        print("-----------------------")
        print("Confession Record End")
        print("-----------------------")


def sr_load():
    global file_name
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
            # print("Load JSON:")
            # print(data)

            if not isinstance(data, list):
                data = [data]

            return data

    except FileNotFoundError:
        print("No JSON")
        return []

    except json.JSONDecodeError:
        print("Wrong JSON")
        return []



def sr_random_speech():
    data = sr_load()
    
    if not data:
        print("No speech to play")
        tts_speak("There isn't any confession")
        return None
    random_speech = random.choice(data).get("speech", "").strip()
    if not random_speech:
        print("Random speech is empty")
        return
    
    tts_speak("This is someone else's confession.")
    time.sleep(4)
    tts_speak(random_speech)   
    
        

def sr_save():
    global listening, speech_data, file_name
    listening = False

    if not speech_data["speech"].strip():
        print("Speech None")
        return

    data = sr_load()
    next_user_number = len(data)

    new_speech_data = {
        "user": next_user_number,
        "speech": speech_data["speech"]
    }

    data.append(new_speech_data)

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"JSON updated: user {next_user_number}")
    speech_data["speech"] = ""

def sr_respond():
    global listening, lms_result, lms_model, last_text,emotion_list,emotion_prompt_1,engine
    listening = False
    lms_result = lms_model.respond(last_text + "/" + emotion_prompt_1 + emotion_list)
    print(lms_result)
    tts_speak("I can feel you are " + str(lms_result))


def write_serial():
    # cmd = "Hello"
    # ser.write((cmd+"\n").encode('utf-8'))
    # print(f"{cmd} write")
    pass

writeTh = th.Thread(target=write_serial, daemon=True)
writeTh.start()


def read_serial():
    global running, userSit
    
    while running:
        if ser.in_waiting>0:
            readSer = ser.readline().decode("utf-8", errors='ignore').strip().lower()
            # if readSer:
            #     print(f"From Arduino {readSer}")
            if readSer == "dooropen":
                # Save confession data
                sr_save()
                # Sequence End
                seq_reset()
            elif readSer == "doorclose":
                seq_start_trigger("door")
            elif readSer == "sit":
                seq_start_trigger("sit")
            elif readSer == "stand":
                userSit = False
                # print("User Stand")
            
            if not waiting:                
                if readSer == "interone":
                    sr_toggle()
                elif readSer == "intertwo":
                    print("Play confession")
                    sr_random_speech()
        else:
            time.sleep(0.01)


readTh = th.Thread(target=read_serial, daemon= True)
readTh.start()

def sr_loop():
    global running, listening, last_text, speech_data, lms_result,mic_index

    with sr.Microphone(device_index=mic_index) as mic:
        # print("MIC open")
        recognizer.adjust_for_ambient_noise(mic, duration = noise_duration)
                
        while running:
            if not listening:
                time.sleep(0.01)
                continue
            try:
                audio = recognizer.listen(mic)
                
                text = recognizer.recognize_google(audio).lower()
                last_text = text
                print(f"Recognized: {text}")
                if speech_data["speech"]:
                    speech_data["speech"] += ". "
                speech_data["speech"] += text


                    
            except sr.UnknownValueError:
                print("Audio not recognized")
                continue

srTh = th.Thread(target=sr_loop, daemon = True)
srTh.start()

def tts_loop():
    global running, engine
    while running:
        try:
            text = tts_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        
        if text is None:
            continue
        try:
            # Pyttsx3 isn't stable in MacOS -> replace with mac internal tts
            # engine.say(text)
            # engine.runAndWait()
            mac_tts_speak(text)
    
            time.sleep(0.2)
        except Exception:
            print(Exception)


ttsTh = th.Thread(target=tts_loop, daemon=True)
ttsTh.start()

def tts_speak(text):
    tts_queue.put(text.strip())
    
def mac_tts_speak(text):
    if text and text.strip():
        subprocess.run(["say", text])
while running:
    cmd = input("CMD: ")
    if cmd == "exit":
        listening = False
        running = False
        break

# while running:
#     cmd = input("Enter cmd: ").strip().lower()
    
#     if cmd == "on":
#         sr_on()
#         # engine.say("Tell me about the emotional thing happened today")
#         # engine.runAndWait()
#         # listening =True
#         # print("Start listening")
#     elif cmd == "off":
#         sr_off()
#         # listening = False
#         # print("Stop listening")
#     elif cmd == "speak":
#         listening = False
#         if last_text:
#             engine.say(last_text)
#             engine.runAndWait()
#         else:
#             print("No text to speak")
#     elif cmd == "save":
#         sr_save()
#         # listening = False
#         # with open("speech_data.json", 'w') as f:
#         #     json.dump(speech_data,f,indent=4)
#     elif cmd == "respond":
#         sr_respond()
#         # listening = False
#         # lms_result = lms_model.respond(last_text + "/" + emotion_prompt_1 + emotion_list)
#         # print(lms_result)
#         # engine.say("I can feel you are " + str(lms_result))
#         # # engine.say(str(lms_result))
#         # engine.runAndWait()


#     elif cmd == "exit":
#         listening = False
#         running = False
#         print("Exit code")

