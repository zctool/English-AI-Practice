from pydub import AudioSegment

def convert_to_wav(input_file, output_file):
    audio = AudioSegment.from_file(input_file, format="m4a")
    audio.export(output_file, format="wav")

if __name__ == "__main__":
    input_file = "recorded_audio.m4a"
    output_file = "recorded_audio.wav"
    convert_to_wav(input_file, output_file)
