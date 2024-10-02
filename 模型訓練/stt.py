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

prompts = [
    "Hey, how are you doing today?",
]

description = "A male teacher with a slightly low-pitched voice, in a very confined sounding environment with clear audio quality. He uses the voice for teaching propose."

input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)

for idx, prompt in enumerate(prompts):
    prompt_input_ids = tokenizer(prompt, return_tensors="pt").input_ids.to(device)
    generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids).to(torch.float32)
    audio_arr = generation.cpu().numpy().squeeze()
    output_filename = f"parler_tts_out_{idx + 1}.wav"
    sf.write(output_filename, audio_arr, model.config.sampling_rate)
    print(f"Generated {output_filename}")

print("All audio files generated successfully.")
