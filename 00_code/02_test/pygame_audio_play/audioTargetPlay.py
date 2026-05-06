import os
import sounddevice as sd
import soundfile as sf
import numpy as np

def list_output_devices():
    devices = sd.query_devices()
    output_devices = []
    
    print("Speaker List: ")
    for idx, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            output_devices.append((idx, device['name']))
            print(f"[{idx}] {device['name']}")
    return output_devices

def play_audio_on_specific_device(folder_path, file_name, device_index):
    full_path = os.path.join(folder_path, file_name)
    
    if not os.path.exists(full_path):
        print(f"error")
        return

    try:
        data, fs = sf.read(full_path)
        
        sd.default.device = device_index
        
        sd.play(data, fs)
        
        sd.wait()
        
    except Exception as e:
        print(e)
        

if __name__ == "__main__":
    available_devices = list_output_devices()
    
    if not available_devices:
        print("No device")
    else:
        try:
            selected_idx = int(input("Select speaker: "))
            
            if any(dev[0] == selected_idx for dev in available_devices):

                current_dir = os.path.dirname(os.path.abspath(__file__))
                
                TARGET_FOLDER = os.path.join(current_dir, "0 audio source")
                
                AUDIO_FILE = "sample.wav" 
                
                play_audio_on_specific_device(TARGET_FOLDER, AUDIO_FILE, selected_idx)
            else:
                print("Invalid number.")
        except ValueError:
            print("Please enter only numbers.")