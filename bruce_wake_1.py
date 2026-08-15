"""
Bruce Wake Word Listener using Vosk
Only triggers on full recognized results, not partials
"""

import pyaudio
import json
import time
import requests
from vosk import Model, KaldiRecognizer

WAKE_PHRASE      = "bruce online"
SAMPLE_RATE      = 16000
CHUNK            = 4000
COOLDOWN_SECONDS = 10
BRUCE_URL        = "http://localhost:9001/activate"

# ── AUDIO SETUP ───────────────────────────────────────────────────────────────
pa = pyaudio.PyAudio()

input_device = None
for i in range(pa.get_device_count()):
    info = pa.get_device_info_by_index(i)
    if "shure" in info["name"].lower() and info["maxInputChannels"] > 0:
        input_device = i
        print(f"[Wake] Using mic: {info['name']}")
        break

if input_device is None:
    print("[Wake] Shure mic not found, using default input")

# ── VOSK SETUP ────────────────────────────────────────────────────────────────
print("[Wake] Loading Vosk model...")
model = Model(model_name="vosk-model-small-en-us-0.15")
rec = KaldiRecognizer(model, SAMPLE_RATE)
print("[Wake] Ready.")

def signal_bruce(retries=12, delay=1.5):
    # Bruce can still be mid-import (torch/Whisper/Kokoro/Pocket TTS are slow
    # to load, especially on a cold start) even after our fixed boot wait
    # above. Retry for a while instead of dropping the wake word on the
    # floor. Widened from 6 retries (~9s) to 12 (~18s) on 2026-08-14 after
    # adding Pocket TTS to the boot sequence pushed real-world boot time past
    # the old window - Banmi hit "Could not reach Bruce" plus a burst of late
    # retries landing all at once after Bruce finally came up.
    for attempt in range(retries):
        try:
            requests.post(BRUCE_URL, timeout=2)
            print("[Wake] Bruce activated!")
            return
        except Exception:
            if attempt < retries - 1:
                time.sleep(delay)
    print("[Wake] Could not reach Bruce.")

def main():
    print("""
╔══════════════════════════════════════════╗
║     BRUCE WAKE WORD LISTENER (Vosk)      ║
║                                          ║
║  Say "Bruce online" to activate          ║
║  Ctrl+C to quit                          ║
╚══════════════════════════════════════════╝
    """)

    print("[Wake] Flushing audio buffer...")
    stream = pa.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                     input=True, input_device_index=input_device, frames_per_buffer=CHUNK)
    for _ in range(20):
        stream.read(CHUNK, exception_on_overflow=False)
    rec.Reset()

    print("[Wake] Waiting 12 seconds for Bruce to boot...")
    time.sleep(12)

    # Flush again after boot wait
    for _ in range(20):
        stream.read(CHUNK, exception_on_overflow=False)
    rec.Reset()

    last_trigger = 0
    print("[Wake] Now listening for 'Bruce online'...\n")
    try:
        requests.post("http://localhost:9001/wake_ready", timeout=2)
    except: pass

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)

            # Only check FULL results, not partials — much more reliable
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower().strip()

                if text:
                    print(f"[Wake] Heard: '{text}'")

                if WAKE_PHRASE in text:
                    now = time.time()
                    if now - last_trigger > COOLDOWN_SECONDS:
                        print(f"[Wake] ✅ Wake word detected!")
                        signal_bruce()
                        last_trigger = now
                        rec.Reset()

    except KeyboardInterrupt:
        print("\n[Wake] Shutting down.")
        stream.stop_stream()
        stream.close()
        pa.terminate()

if __name__ == "__main__":
    main()
