from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf
import torch

device = "cpu"
if torch.cuda.is_available():
    device = "cuda"
if torch.backends.mps.is_available():
    device = "mps"
if torch.xpu.is_available():
    device = "xpu"

print('device: ', device)
torch_dtype = torch.float16 if device != "cpu" else torch.float32

model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler_tts_mini_v0.1").to(device, dtype=torch_dtype)
tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler_tts_mini_v0.1")

prompt = "Hey, how are you doing today?"
prompt = "Two days after being tapped as Donald Trump’s running mate, Ohio Sen. JD Vance introduced himself to voters in a speech that highlighted the populist direction the two aim to take the Republican Party — and the nation."
description = "A male teacher with a slightly low-pitched voice, in a very confined sounding environment with clear audio quality. He uses the voice for teaching propose."

input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
prompt_input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)

generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids).to(torch.float32)
audio_arr = generation.cpu().numpy().squeeze()
sf.write("parler_tts_out_man.wav", audio_arr, model.config.sampling_rate)