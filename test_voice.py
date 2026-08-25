from kokoro import KPipeline
import soundfile as sf

print("Loading Orion voice...")

pipeline = KPipeline(lang_code="a")

text = "Hello sir. I am Orion, your personal AI assistant."

generator = pipeline(
    text,
    voice="af_heart",
    speed=1.0
)

for i, (gs, ps, audio) in enumerate(generator):
    filename = f"orion_voice_{i}.wav"

    sf.write(
        filename,
        audio,
        24000
    )

    print("Generated:", filename)

print("Voice generation complete.")