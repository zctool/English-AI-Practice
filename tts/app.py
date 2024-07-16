import os
import pyttsx3
from pydub import AudioSegment

# Define the output directory
output_dir = r"C:\Users\ntubimd\Desktop\tts\mp3"
os.makedirs(output_dir, exist_ok=True)

# Initialize the TTS engine
engine = pyttsx3.init()

# Function to generate and save speech
def generate_and_save_speech(text, file_name):
    # Set the voice (optional)
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)  # Change index to use different voices

    # Save the audio to a WAV file
    wav_path = os.path.join(output_dir, f"{file_name}.wav")
    mp3_path = os.path.join(output_dir, f"{file_name}.mp3")
    engine.save_to_file(text, wav_path)
    engine.runAndWait()

    # Convert WAV to MP3 using pydub
    AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3")
    print(f"Audio file saved as {mp3_path}")

# Text to be converted to speech
text = "Hello, this is a test of the TTS model with a smoother and more natural voice."

# Generate and save speech

generate_and_save_speech(text, file_name="output_smooth_voice")
