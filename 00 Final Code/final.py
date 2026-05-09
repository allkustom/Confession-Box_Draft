import threading as th
import speech_recognition as sr
import json
import serial
import serial.tools.list_ports
import time
import random
import queue
import os
import requests
import wave
import numpy as np
import sounddevice as sd
import soundfile as sf
import argparse
import asyncio
from pythonosc import udp_client


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# TD music sound variables
music_volume_default  = 1.0
music_volume_mid = 0.5
music_volume_min = 0.15

# Connect with TD via OSC
oscClient = udp_client.SimpleUDPClient("127.0.01", 8000)
oscClient.send_message("/musicTrig", False)
oscClient.send_message("/volume", 0.0)


# Arduino Port Setting
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


# Speaker Device Setting
speaker_list = sd.query_devices()
output_speakers = []
print("Speaker List: ")

for i, name in enumerate(speaker_list):
    if name['max_output_channels'] > 0:
        output_speakers.append((i, name['name']))
        print(f"[{i}] {name['name']}")
speaker_index = int(input("Selecet Speaker Index: ").strip())    

# Audio File Path and List
audio_file_folder = "0 audio source"
audio_file_list = [
    "0 intro.wav",
    "1 outro.wav",
    "2 QHappy.wav",
    "3 QSad.wav",
    "4 QFear.wav",
    "5 QDisgust.wav",
    "6 QSurprise.wav",
    "7 QAnger.wav"
]

# Mic Device Setting
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

# TTS Model parameters
MAX_TOKENS = 10000
TEMPERATURE = 0.7
TOP_P = 0.9
REPETITION_PENALTY = 1.1
SAMPLE_RATE = 24000  # SNAC model uses 24kHz
AVAILABLE_VOICES = ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"]
DEFAULT_VOICE = "zac"

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
allow_button = False


last_text = ""


print("--------------")
print("--------------")
print("--------------")
print("PROGRAM READY")
print("--------------")
print("--------------")
print("--------------")



# Speech Recogniation Parameters Setting
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

# Queuing for TTS
tts_queue = queue.Queue()


# Speech Data Form
speech_data = {
    "user": 0,
    "speech": ""
}
file_name = "speech_data.json"
speech_random_executed = []

# Emotion Categories
emotion_list = ["happy", "sad", "fear", "disgust", "surprise", "anger"]
selected_emotion = ""


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# Trigger 'seq_start()' based on the two limit switches' status
def seq_start_trigger(case):
    global waiting, doorClosed, userSit, oscClient
    
    if case == "door":
        doorClosed = True
        print("door closed")
    elif case == "sit":
        userSit = True
        print("user sit")
    
    if doorClosed and userSit:
        if waiting:
            print("Seq start")
            waiting = False
            seq_start()
        
    # else:
    #     waiting = True

def seq_start():
    global oscClient, selected_emotion, emotion_list, allow_button

    write_serial("lightoff")
    time.sleep(3)
    selected_emotion = random.choice(emotion_list)

    oscClient.send_message("/musicTrig", True)
    oscClient.send_message("/volume", music_volume_mid)
    

    sr_random_speech()
    time.sleep(5)
    audio_play(0)
    # time.sleep(2)
    oscClient.send_message("/volume", music_volume_min)
    target_audio_index = emotion_list.index(selected_emotion) + 2
    audio_play(target_audio_index)
    write_serial("leddefault")
    time.sleep(2)
    oscClient.send_message("/volume", music_volume_default)
    allow_button = True
    
    
def seq_reset():
    global listening, last_text, waiting, doorClosed, userSit, oscClient, speech_random_executed, selected_emotion, speech_data


    # Save confession data
    sr_save()
    
    # TD reset setting
    oscClient.send_message("/musicTrig", False)
    oscClient.send_message("/volume", 0.0)
    
    write_serial("lighton")
    write_serial("ledoff")
    print("On waiting")
    listening = False
    last_text= ""
    speech_data = {"user": 0, "speech": ""}
    waiting = True
    doorClosed = False
    userSit = False
    speech_random_executed = []
    selected_emotion = ""


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Toggle the speech recognition on/off when the left button is pressed, and save the confession data when toggled off
def sr_toggle():
    global listening , last_text, speech_data, oscClient, allow_button

    if allow_button:        
        listening = not listening

        if listening:
            oscClient.send_message("/volume", music_volume_min)
            write_serial("ledblink")
            print("-----------------------")
            print("Confession Record Start")
            print("-----------------------")
        else:
            # write_serial("leddefault")
            write_serial("ledoff")
            allow_button = False;
            print("-----------------------")
            print("Confession Record End")
            print("-----------------------")
            time.sleep(3)
            oscClient.send_message("/volume", music_volume_mid)
            audio_play(1)
            time.sleep(1)
            oscClient.send_message("/musicTrig", True)
            oscClient.send_message("/volume", music_volume_default)

# Load the speech data
def sr_load():
    global file_name, emotion_list
    
    default_data = {emotion: [] for emotion in emotion_list}
    
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)

            if not isinstance(data, dict):
                # data = [data]
                return default_data

            return data

    except FileNotFoundError:
        print("No JSON")
        return default_data

    except json.JSONDecodeError:
        print("Wrong JSON")
        return default_data


# Play the random speech data from the targeted JSON file
# Used 'random_speech_executed' to make sure to play different speech
def sr_random_speech():
    global oscClient, speech_random_executed, selected_emotion
    
    full_data = sr_load()
    
    if not selected_emotion or selected_emotion not in full_data:
        print("Selected emotion not found in data")
        return None
        
    data = full_data[selected_emotion]
    
    if not data:
        print("No speech to play")
        return None

    all_index = set(range(len(data)))
    execued_index = set(speech_random_executed)
    remaining_index = list(all_index - execued_index)
    
    if not remaining_index:
        speech_random_executed.clear()
        remaining_index = list(all_index)
    
    random_number = random.choice(remaining_index)
    speech_random_executed.append(random_number)
    random_speech = data[random_number].get("speech", "").strip()
    
    if not random_speech:
        print("Speech is empty")
        return
    
    print("Playing random speech:", random_speech)
    tts_speak_instant(random_speech)

        
# Save the recorded speech data into the targeted JSON file
# when the user left the box
def sr_save():
    global listening, speech_data, file_name, selected_emotion
    listening = False

    if not speech_data["speech"].strip():
        print("Speech None")
        return

    data = sr_load()
    
    if not selected_emotion:
        selected_emotion = random.choice(emotion_list)
        
    next_user_number = len(data[selected_emotion])

    new_speech_data = {
        "user": next_user_number,
        "speech": speech_data["speech"]
    }

    data[selected_emotion].append(new_speech_data)

    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"JSON updated: [{selected_emotion}] user {next_user_number}")
    speech_data["speech"] = ""


# Send/write Serial message to Arduino
def write_serial(cmd = ""):
    global ser
    ser.write((cmd+"\n").encode('utf-8'))
    print(f"{cmd} write")


writeTh = th.Thread(target=write_serial, daemon=True)
writeTh.start()
write_serial("lighton")
write_serial("ledoff")


# Read Serial message from Arduino
def read_serial():
    global running, userSit
    
    while running:
        if ser.in_waiting>0:
            readSer = ser.readline().decode("utf-8", errors='ignore').strip().lower()
            if readSer == "dooropen":
                seq_reset()
            elif readSer == "doorclose":
                seq_start_trigger("door")
            elif readSer == "sit":
                seq_start_trigger("sit")
            # elif readSer == "stand":
            #     userSit = False
            
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

# Speech recognition with non-blocking strcuture
def sr_loop():
    global running, listening, last_text, speech_data, mic_index

    with sr.Microphone(device_index=mic_index) as mic:
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


# Start generating TTS audio 
# when the new prompt is queued
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
            tts_speak_instant(text)
    
            time.sleep(0.2)
        except Exception as e:
            print("tts_loop error:", e)


ttsTh = th.Thread(target=tts_loop, daemon=True)
ttsTh.start()


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Orpheus-TTS
# Github Link: https://github.com/isaiahbjork/orpheus-tts-local

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




# Revised version, for handling the audio chunk
# ------------------------------------------------------------------
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
    
    prompt = args.text
    output_file = args.output

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

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# Play the audio file from the targeted audio file
def audio_play(file_index = 0):
    global speaker_index, audio_file_folder,audio_file_list
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    TARGET_FOLDER = os.path.join(current_dir, audio_file_folder)
    
    if file_index < 0 or file_index >= len(audio_file_list):
        print("Audio file index, out of range")
        return
    AUDIO_FILE = audio_file_list[file_index]
    play_audio_on_specific_device(TARGET_FOLDER, AUDIO_FILE, speaker_index)
    

def play_audio_on_specific_device(folder_path, file_name, device_index):
    full_path  = os.path.join(folder_path, file_name)
    if not os.path.exists(full_path):
        print("File not found:", full_path)
        return
    try:
        data, fs = sf.read(full_path)
        sd.default.device = device_index
        
        sd.play(data,fs)
        sd.wait()
    except Exception as e:
        print(f"Audio Play Error: {e}")
    

# Queuing the prompt for TTS generation
def tts_speak_queue(text):
    tts_queue.put(text.strip())
    
# Generating the TTS instantly
# This feature is blocking function
def tts_speak_instant(text):
    audio_segments = generate_speech_from_api(
        prompt=text
    )

# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# default running
# Exit the code throught type 'exit'
while running:
    cmd = input("CMD: ")
    if cmd == "exit":
        listening = False
        running = False
        break
    
    
    