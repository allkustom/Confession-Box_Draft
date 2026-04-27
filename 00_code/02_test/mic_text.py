import threading as th
import speech_recognition as sr
import pyttsx3
import json
import lmstudio as lms

lms_model = lms.llm("qwen/qwen3-4b-2507")


running = True
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
noise_duration = 0.5

# rate = engine.getProperty('rate')
# print (rate)
# engine.setProperty('rate', 125)  

# voices = engine.getProperty('voices')
# engine.setProperty('voice', voices[1].id) 



speech_data = {
    "user": "",
    "speech": ""
}

speech_data["user"] = input("Enter user name: ")


print("----- CMD list -----")
print("'on' - start recording")
print("'off' - stop recording")
print("'speak' - voice based on the recorded speech")
print("'save' - save the speech data as JSON")
print("'exit' - quit code")


def sr_loop():
    global running, listening, last_text, speech_data, lms_result

    with sr.Microphone() as mic:
        # print("MIC open")
                
        while running:
            if not listening:
                continue
            try:
                recognizer.adjust_for_ambient_noise(mic, duration = noise_duration)
                audio = recognizer.listen(mic)
                
                text = recognizer.recognize_google(audio)
                text = text.lower()
                last_text = text
                print(f"Recognized: {text}")
                speech_data["speech"] += text


                    
            except sr.UnknownValueError:
                print("Audio not recognized")
                continue

th = th.Thread(target=sr_loop, daemon = True)
th.start()


while running:
    cmd = input("Enter cmd: ").strip().lower()
    
    if cmd == "on":
        engine.say("Tell me about the emotional thing happened today")
        engine.runAndWait()
        listening =True
        print("Start listening")
    elif cmd == "off":
        listening = False
        print("Stop listening")
    elif cmd == "speak":
        listening = False
        if last_text:
            engine.say(last_text)
            engine.runAndWait()
        else:
            print("No text to speak")
    elif cmd == "save":
        listening = False
        with open("speech_data.json", 'w') as f:
            json.dump(speech_data,f,indent=4)
    elif cmd == "respond":
        listening = False
        lms_result = lms_model.respond(last_text + "/" + emotion_prompt_1 + emotion_list)
        print(lms_result)
        engine.say("I can feel you are " + str(lms_result))
        # engine.say(str(lms_result))
        engine.runAndWait()


    elif cmd == "exit":
        listening = False
        running = False
        print("Exit code")

# while True:
#     try:
#         with sr.Microphone() as mic:
#             recognizer.adjust_for_ambient_noise(mic, duration = noise_duration)
#             audio = recognizer.listen(mic)
            
#             text = recognizer.recognize_google(audio)
#             text = text.lower()
#             print(f"Recognized: {text}")
            
#     except sr.UnknownValueError:
#         recognizer = sr.Recognizer()
#         print("Could not understand audio, trying again...")
#         continue

