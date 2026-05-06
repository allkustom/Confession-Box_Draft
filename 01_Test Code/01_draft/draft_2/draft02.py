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

import os
import sys
import requests
import wave
import numpy as np
import sounddevice as sd
import argparse
import asyncio
from pythonosc import udp_client

oscClient = udp_client.SimpleUDPClient("127.0.01", 8000)
# oscClient.send_message("/bool", True)
oscClient.send_message("/ghost", 1)
oscClient.send_message("/musicTrig", False)


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
# lms_model = lms.llm("gemma-4-26b-a4b-it")

mic_list = sr.Microphone.list_microphone_names()
print("Mic List: ")
for i, name in enumerate(mic_list):
    print(f"[{i}] {name}")
mic_index = int(input("Select Mic Index: ").strip())

# LM Studio API settings
API_URL = "http://127.0.0.1:1234/v1/completions"
HEADERS = {
    "Content-Type": "application/json"
}

# Model parameters
MAX_TOKENS = 2500
TEMPERATURE = 0.7
# TEMPERATURE = random.uniform(0.8, 1.5)
TOP_P = 0.9
REPETITION_PENALTY = 1.1
# REPETITION_PENALTY = random.uniform(1.1,1.5)
SAMPLE_RATE = 24000  # SNAC model uses 24kHz

# Available voices based on the Orpheus-TTS repository
AVAILABLE_VOICES = ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"]
DEFAULT_VOICE = "zac"
# DEFAULT_VOICE = random.choice(AVAILABLE_VOICES)

# Special token IDs for Orpheus model
START_TOKEN_ID = 128259
END_TOKEN_IDS = [128009, 128260, 128261, 128257]
CUSTOM_TOKEN_PREFIX = "<custom_token_"


# Operating statements
running = True
waiting = True 
doorClosed = False
userSit = False
listening = False




# engine = pyttsx3.init()
last_text = ""
# total_text = ""
# emotion_prompt_1 = "Tell me a single word that describe the emotion of what I said. Based on the following emotion list"
emotion_prompt_1 = "Choose one emtion from the following emotion list based on what I just said. (Answer with just the selected emotion in one word)"
emotion_list = "happy / sad / fear / disgust / surprise / anger"


# If want to put variable in this pormpt, use 'f' and {}
confession_prompt_1 = """
[Task]
Grade the user’s recording on how deep the message was from 0-100 based on the sincerity of their confession (Anxiety, Regret, or Sin). 
X equals the user's deep rating.

[Scoring Rubric - STRICT]
- X < 30: Topic is NOT about anxiety, regret, or sin. Or it is too brief/vague.
- 30 <= X < 60: Content is about regret/sin, but lacks specific context or details. (Hard Ceiling: Max 60 for low context).
- 70 <= X: Sincere confession with clear context, specific events, and deep emotion.

[Output Format Rule] - STRICT ADHERENCE REQUIRED
Your response must follow this exact format: Score///Content
- Do NOT summarize the user's input.
- Do NOT repeat what the user just said.
- Do NOT provide any analysis or introductory remarks.
- Example: 45///Could you share more about the specific situation that made you feel this way?

[Response Logic]
Based on the score 'X', generate the (Content) in English (Max 2 sentences):

1. If X < 70 (Encouragement):
   Directly ask a question to pull out more details about their sin, regret, or anxiety. 
   Do NOT say "You feel..." or "So you are saying...". Just ask the question.

2. If X >= 70 (Completion):
   Provide a warm, reassuring statement and ask if they are ready to hear another confession.
   Example: "Thank you for sharing your truth. Would you like to hear a confession from someone else now?"

[Constraints]
- NO SUMMARY: Never summarize or paraphrase the user's message.
- NO REPETITION: Do not repeat any words the user used in their confession.
- Topic: Only give high scores for topics related to Sin, Regret, or Anxiety.
- Limit: Max 2 sentences for Content. 
- Question Limit: On the 3rd interaction, give X=85 and use the (X >= 70) logic.

[Final Reminder]
Format: Score///Content. No summary, no analysis, no extra text.
"""


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
recognizer.pause_threshold = 0.8
recognizer.non_speaking_duration = 0.8
recognizer.phrase_threshold = 0.3
noise_duration = 0.5
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






def seq_start_trigger(case):
    global waiting, doorClosed, userSit, oscClient
    
    if case == "door":
        doorClosed = True
        print("door closed")
    elif case == "sit":
        userSit = True
        print("user sit")
    
    if doorClosed and userSit:
        waiting = False
        print("Seq start")
        
        seq_start()
        
    else:
        waiting = True
        # print("On waiting")
        # write_serial("lighton")
        # oscClient.send_message("/ghost", False)


def seq_start():
    global oscClient
    write_serial("lightoff")
    time.sleep(2)
    write_serial("ledlon")
    write_serial("ledron")

    

    # TD Pepper's ghost control
    # Turn on the visual and reset the variables
    oscClient.send_message("/ghost", 0)
    oscClient.send_message("/musicTrig", True)
    oscClient.send_message("/volume", 0.1)
    
    tts_speak_instant("Disclaimer! Your confession will be recorded but your voice will be altered. Your identity will remain anonymous. When done, to stop recording, hit the left button again.")


    tts_speak_instant("Hey, this is a sensory box. In it, we want you to reflect and share what has recently been on your mind. In this box we will take note of responses, but not share any personal information.")
    # tts_speak_instant("Hey, this is a sensory box.")
    # tts_speak_instant("In it, we want you to reflect and share what has recently been on your mind.")
    # tts_speak_instant("In this box we will take note of responses, but not share any personal information.")


    
    tts_speak_instant("If you would like to share a confession of your own, press the left button.") 
    write_serial("ledloff")
    write_serial("ledroff")
    write_serial("ledlon")
    tts_speak_instant("If you would like to hear a previous confession, press the right button.")
    write_serial("ledloff")
    write_serial("ledron")
    
    time.sleep(2)
    write_serial("ledroff")
    oscClient.send_message("/musicTrig", True)
    oscClient.send_message("/volume", 0.3)
    
    
def seq_reset():
    global listening, last_text, waiting, doorClosed, userSit, oscClient, DEFAULT_VOICE


    # Save confession data
    sr_save()
    
    # TD reset setting
    oscClient.send_message("/ghost", 1)
    oscClient.send_message("/musicTrig", False)
    
    write_serial("lighton")
    print("On waiting")
    listening = False
    last_text= ""
    speech_data["speech"] = ""
    waiting = True
    doorClosed = False
    userSit = False
    # DEFAULT_VOICE = random.choice(AVAILABLE_VOICES)

def sr_toggle():
    global listening, lms_result,confession_prompt_1 , last_text, lms_model, speech_data
    
    if speech_data["speech"] == "" and not listening:
            oscClient.send_message("/volume", 0.1)
            # tts_speak_instant("Disclaimer! Your confession will be recorded but your voice will be altered. Your identity will remain anonymous. When done, to stop recording, hit the left button again.")
            oscClient.send_message("/musicTrig", False)
            # tts_speak_instant("Disclaimer!")
            # tts_speak_instant("Your confession will be recorded but your voice will be altered. Your identity will remain anonymous.")
            # tts_speak_instant("When done, to stop recording, hit the left button again.")
    listening = not listening

    if listening:
        oscClient.send_message("/musicTrig", False)
        write_serial("ledlon")
        print("-----------------------")
        print("Confession Record Start")
        print("-----------------------")
    else:
        write_serial("ledloff")
        print("-----------------------")
        print("Confession Record End")
        print("-----------------------")
        lms_result = lms_model.respond(speech_data["speech"] + "/" + confession_prompt_1)
        result_split = lms_result.content.strip().split("///")
        # result_split = str(lms_result).strip().split("///")

        if len(result_split) >= 2:
            score = int(result_split[0].strip())
            message = result_split[1].strip()
            print(f"AI Score: {score}")
            print(f"AI Message: {message}")
            
            tts_speak_instant(message)
        else:
            print(f"AI answered in a wrong structure: {lms_result}")
        
        oscClient.send_message("/musicTrig", True)
        oscClient.send_message("/volume", 0.3)
        
        # Send test to AI and get response
        
        


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
    global oscClient
    
    data = sr_load()
    
    if not data:
        print("No speech to play")
        # tts_speak_queue("There isn't any confession")
        return None
    random_speech = random.choice(data).get("speech", "").strip()
    if not random_speech:
        # print("Random speech is empty")
        return
    
    oscClient.send_message("/musicTrig", False)
    write_serial("ledron")
    tts_speak_instant("This is someone else's confession.")
    time.sleep(2)
    if random_speech and random_speech.strip():
        random_speech_split = random_speech.split(". ")
        for i in random_speech_split:
            if i.strip():
                tts_speak_instant(i.strip())
    time.sleep(2)
    tts_speak_instant("After hearing this, how do you feel? ... If you have anything you would like to add, press the left button")
    time.sleep(2)
    oscClient.send_message("/musicTrig", True)
    oscClient.send_message("/volume", 0.3)
    write_serial("ledloff")
        

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
    tts_speak_instant("I can feel you are " + str(lms_result))
    # tts_speak_queue("I can feel you are " + str(lms_result))


def write_serial(cmd = ""):
    global ser
    # cmd = "Hello"
    ser.write((cmd+"\n").encode('utf-8'))
    print(f"{cmd} write")
    # pass


writeTh = th.Thread(target=write_serial, daemon=True)
writeTh.start()
write_serial("lighton")


def read_serial():
    global running, userSit
    
    while running:
        if ser.in_waiting>0:
            readSer = ser.readline().decode("utf-8", errors='ignore').strip().lower()
            # if readSer:
            #     print(f"From Arduino {readSer}")
            if readSer == "dooropen":
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
            tts_speak_instant(text)
    
            time.sleep(0.2)
        except Exception as e:
            print("tts_loop error:", e)


ttsTh = th.Thread(target=tts_loop, daemon=True)
ttsTh.start()






# -----------------------------
# -----------------------------
# Orpheus

def format_prompt(prompt, voice=DEFAULT_VOICE):
    """Format prompt for Orpheus model with voice prefix and special tokens."""
    if voice not in AVAILABLE_VOICES:
        print(f"Warning: Voice '{voice}' not recognized. Using '{DEFAULT_VOICE}' instead.")
        voice = DEFAULT_VOICE
        
    # Format similar to how engine_class.py does it with special tokens
    formatted_prompt = f"{voice}: {prompt}"
    
    # Add special token markers for the LM Studio API
    special_start = "<|audio|>"  # Using the additional_special_token from config
    special_end = "<|eot_id|>"   # Using the eos_token from config
    
    return f"{special_start}{formatted_prompt}{special_end}"

def generate_tokens_from_api(prompt, voice=DEFAULT_VOICE, temperature=TEMPERATURE, 
                            top_p=TOP_P, max_tokens=MAX_TOKENS, repetition_penalty=REPETITION_PENALTY):
    """Generate tokens from text using LM Studio API."""
    formatted_prompt = format_prompt(prompt, voice)
    print(f"Generating speech for: {formatted_prompt}")
    
    # Create the request payload for the LM Studio API
    payload = {
        # "model": "orpheus-3b-0.1-ft-q4_k_m",  # Model name can be anything, LM Studio ignores it
        "model": "orpheus-3b-0.1-ft",  # Model name can be anything, LM Studio ignores it
        "prompt": formatted_prompt,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "repeat_penalty": repetition_penalty,
        "stream": True
    }
    
    # Make the API request with streaming
    response = requests.post(API_URL, headers=HEADERS, json=payload, stream=True)
    
    if response.status_code != 200:
        print(f"Error: API request failed with status code {response.status_code}")
        print(f"Error details: {response.text}")
        return
    
    # Process the streamed response
    token_counter = 0
    for line in response.iter_lines():
        if line:
            line = line.decode('utf-8')
            if line.startswith('data: '):
                data_str = line[6:]  # Remove the 'data: ' prefix
                if data_str.strip() == '[DONE]':
                    break
                    
                try:
                    data = json.loads(data_str)
                    if 'choices' in data and len(data['choices']) > 0:
                        token_text = data['choices'][0].get('text', '')
                        token_counter += 1
                        if token_text:
                            yield token_text
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON: {e}")
                    continue
    
    print("Token generation complete")

def turn_token_into_id(token_string, index):
    """Convert token string to numeric ID for audio processing."""
    # Strip whitespace
    token_string = token_string.strip()
    
    # Find the last token in the string
    last_token_start = token_string.rfind(CUSTOM_TOKEN_PREFIX)
    
    if last_token_start == -1:
        return None
    
    # Extract the last token
    last_token = token_string[last_token_start:]
    
    # Process the last token
    if last_token.startswith(CUSTOM_TOKEN_PREFIX) and last_token.endswith(">"):
        try:
            number_str = last_token[14:-1]
            token_id = int(number_str) - 10 - ((index % 7) * 4096)
            return token_id
        except ValueError:
            return None
    else:
        return None

def convert_to_audio(multiframe, count):
    """Convert token frames to audio."""
    # Import here to avoid circular imports
    from decoder import convert_to_audio as orpheus_convert_to_audio
    return orpheus_convert_to_audio(multiframe, count)

async def tokens_decoder(token_gen):
    """Asynchronous token decoder that converts token stream to audio stream."""
    buffer = []
    count = 0
    async for token_text in token_gen:
        token = turn_token_into_id(token_text, count)
        if token is not None and token > 0:
            buffer.append(token)
            count += 1
            
            # Convert to audio when we have enough tokens
            if count % 7 == 0 and count > 27:
                buffer_to_proc = buffer[-28:]
                audio_samples = convert_to_audio(buffer_to_proc, count)
                if audio_samples is not None:
                    yield audio_samples




# Revised version, for handling the chunk------------------------------------------------------------------
def tokens_decoder_sync(syn_token_gen, output_file=None, play_audio_output=True):
    audio_queue = queue.Queue()
    audio_segments = []

    wav_file = None
    if output_file:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        wav_file = wave.open(output_file, "wb")
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)

    async def async_token_gen():
        for token in syn_token_gen:
            yield token

    async def async_producer():
        async for audio_chunk in tokens_decoder(async_token_gen()):
            audio_queue.put(audio_chunk)
        audio_queue.put(None)

    def run_async():
        asyncio.run(async_producer())

    decoderTh = th.Thread(target=run_async)
    decoderTh.start()

    while True:
        audio = audio_queue.get()
        if audio is None:
            break

        audio_segments.append(audio)

        if wav_file:
            wav_file.writeframes(audio)

    if wav_file:
        wav_file.close()

    decoderTh.join()

    if play_audio_output and audio_segments:
        full_audio = b"".join(audio_segments)
        stream_audio(full_audio)

    duration = sum(len(segment) // 2 for segment in audio_segments) / SAMPLE_RATE
    print(f"Generated {len(audio_segments)} audio segments")
    print(f"Generated {duration:.2f} seconds of audio")

    return audio_segments


def stream_audio(audio_buffer):
    if audio_buffer is None or len(audio_buffer) == 0:
        return

    audio_data = np.frombuffer(audio_buffer, dtype=np.int16)
    audio_float = audio_data.astype(np.float32) / 32767.0
    sd.play(audio_float, SAMPLE_RATE)
    sd.wait()

def generate_speech_from_api(prompt, voice=DEFAULT_VOICE, output_file=None, play_audio_output=True,
                     temperature=TEMPERATURE, top_p=TOP_P, max_tokens=MAX_TOKENS,
                     repetition_penalty=REPETITION_PENALTY):
    """Generate speech from text using Orpheus model via LM Studio API."""
    return tokens_decoder_sync(
        generate_tokens_from_api(
            prompt=prompt, 
            voice=voice,
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            repetition_penalty=repetition_penalty
        ),
        output_file=output_file,
        play_audio_output=play_audio_output
    )
    
    
def list_available_voices():
    """List all available voices with the recommended one marked."""
    print("Available voices (in order of conversational realism):")
    for i, voice in enumerate(AVAILABLE_VOICES):
        marker = "★" if voice == DEFAULT_VOICE else " "
        print(f"{marker} {voice}")
    print(f"\nDefault voice: {DEFAULT_VOICE}")
    
    print("\nAvailable emotion tags:")
    print("<laugh>, <chuckle>, <sigh>, <cough>, <sniffle>, <groan>, <yawn>, <gasp>")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Orpheus Text-to-Speech using LM Studio API")
    parser.add_argument("--text", type=str, help="Text to convert to speech")
    parser.add_argument("--voice", type=str, default=DEFAULT_VOICE, help=f"Voice to use (default: {DEFAULT_VOICE})")
    parser.add_argument("--output", type=str, help="Output WAV file path")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    parser.add_argument("--temperature", type=float, default=TEMPERATURE, help="Temperature for generation")
    parser.add_argument("--top_p", type=float, default=TOP_P, help="Top-p sampling parameter")
    parser.add_argument("--repetition_penalty", type=float, default=REPETITION_PENALTY, 
                       help="Repetition penalty (>=1.1 required for stable generation)")
    
    args = parser.parse_args()
    
    if args.list_voices:
        list_available_voices()
        return
    
    # Use text from command line or prompt user
    prompt = args.text
    # if not prompt:
    #     if len(sys.argv) > 1 and sys.argv[1] not in ("--voice", "--output", "--temperature", "--top_p", "--repetition_penalty"):
    #         prompt = " ".join([arg for arg in sys.argv[1:] if not arg.startswith("--")])
    #     else:
    #         prompt = input("Enter text to synthesize: ")
    #         if not prompt:
    #             prompt = "Hello, I am Orpheus, an AI assistant with emotional speech capabilities."
    
    # Default output file if none provided
    output_file = args.output
    # if not output_file:
    #     # Create outputs directory if it doesn't exist
    #     os.makedirs("outputs", exist_ok=True)
    #     # Generate a filename based on the voice and a timestamp
    #     timestamp = time.strftime("%Y%m%d_%H%M%S")
    #     output_file = f"outputs/{args.voice}_{timestamp}.wav"
    #     print(f"No output file specified. Saving to {output_file}")
    
    # Generate speech
    start_time = time.time()
    audio_segments = generate_speech_from_api(
        prompt=prompt,
        voice=args.voice,
        temperature=args.temperature,
        top_p=args.top_p,
        repetition_penalty=args.repetition_penalty,
        output_file=output_file,
        play_audio_output=True
    )
    end_time = time.time()
    
    print(f"Speech generation completed in {end_time - start_time:.2f} seconds")
    print(f"Audio saved to {output_file}")

# if __name__ == "__main__":
#     main() 
    


# ---------------------------------------
# ---------------------------------------
# default runing


def tts_speak_queue(text):
    tts_queue.put(text.strip())
    
def tts_speak_instant(text):
    audio_segments = generate_speech_from_api(
        prompt=text
    )
    # if text and text.strip():
    #     subprocess.run(["say", text])
while running:
    cmd = input("CMD: ")
    if cmd == "exit":
        listening = False
        running = False
        break