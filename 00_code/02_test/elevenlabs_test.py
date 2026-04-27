# from dotenv import load_dotenv
# from elevenlabs.client import ElevenLabs
# from elevenlabs.play import play

# load_dotenv()

# elevenlabs = ElevenLabs()

# audio = elevenlabs.text_to_speech.convert(
#     text="The first move is what sets everything in motion.",
#     voice_id="JBFqnCBsd6RMkjVDRZzb",
#     model_id="eleven_v3",
#     output_format="mp3_44100_128",
# )

# play(audio)

from google.cloud import texttospeech 

client = texttospeech.TextToSpeechAsyncClient()

synthesis_input = texttospeech.SynthesisInput(text = "Hello, World!")

voice = texttospeech.VoiceSelectionParams(
    language_code = "en-US",
    ssml_gender = texttospeech.SsmlVoiceGender.NEUTRAL,
)

audio_config = texttospeech.AudioConfig(
    audio_encoding = texttospeech.AudioEncoding.MP3
)

response = client.synthesize_speech(
    input = synthesis_input, voice= voice, audio_config= audio_config
)

with open("output.mp3", "wb") as out:
    out.write(response.audio_content)
    print("Audio saved")