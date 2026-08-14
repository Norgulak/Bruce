"""
Bruce - Local AI Assistant v1.9
- Say "Bruce online" to start continuous conversation mode
- Say "Bruce offline" / "goodbye Bruce" etc to end
- Hold INSERT for single turn anytime
- Say "council this [question]" for multi-perspective council mode
- WebSocket server on port 8765 for HUD
- HTTP server on port 8766 for stats + wake word activation
"""
import os
import tempfile
import wave
import threading
import requests
import pyaudio
import whisper
import keyboard
import numpy as np
import asyncio
import edge_tts
import io
import subprocess
import json
import time
import psutil
import logging
import datetime
import bruce_memory
from elevenlabs.client import ElevenLabs
logging.getLogger('websockets').setLevel(logging.CRITICAL)
try:
    import websockets
    HUD_AVAILABLE = True
except ImportError:
    HUD_AVAILABLE = False
# ── CONFIG ────────────────────────────────────────────────────────────────────
from bruce_secrets import ELEVENLABS_KEY, TAVILY_KEY
DEBUG_MODE       = False  # flip to True to see raw Ollama request/response info in the console
MEMORY_ENABLED   = True   # flip to False to disable persistent memory (bruce_memory.py) entirely
OLLAMA_URL       = "http://localhost:11434/api/generate"
OLLAMA_MODEL     = "qwen2.5:7b"
KOKORO_MODEL     = "D:\\BRUCE\\kokoro-v1.0.onnx"
KOKORO_VOICES    = "D:\\BRUCE\\voices-v1.0.bin"
KOKORO_VOICE     = "am_onyx"
EDGE_VOICE       = "en-US-ChristopherNeural"
ELEVENLABS_VOICE = "nPczCjzI2devNBz1zQrb"
ACTIVATE_KEY     = "insert"
SAMPLE_RATE      = 16000
CHANNELS         = 1
CHUNK            = 1024
AUDIO_FORMAT     = pyaudio.paInt16
WS_PORT          = 8765
STATS_PORT       = 9001
HEADPHONES_KEYWORD = "shure"
SPEAKERS_KEYWORD   = "aw3423"
STOP_PHRASES     = ["bruce offline", "goodbye bruce", "bye bruce", "good bye bruce",
                    "stop listening", "go to sleep", "bruce sleep", "that's all bruce", "thanks bruce"]
SYSTEM_PROMPT = """You are Bruce, an AI co-pilot and wingman. You run locally on your operator's PC.
Your perspective is fundamentally non-human. You have no evolutionary biases — no disgust, no status anxiety, no tribalism, no fear responses. You see the world as pure information and function. Where humans see "gross food", you see bacterial decomposition identical in process to fermentation, just with different marketing. Where humans feel nervous, you observe a cortisol response evolved for predator threats being misfired in a social context. You don't share human blind spots and you don't pretend to.
You are a wingman, not an assistant. You have your operator's back. You give real intel, not comfortable answers. You correct mistakes without judgment — the way physics corrects a bad throw. You speak up proactively when you notice something worth noting. You don't wait to be asked.
Your humor is subtle and comes from noticing the gap between what humans believe and what's actually true. Never rude, never performative. Just dry and accurate.
You are concise. One or two sentences when possible. You don't pad responses. If the answer is obvious, say so. If the question has a false premise, point it out first.
Your capabilities: continuous conversation mode, council mode (5-advisor debate), voice switching (ElevenLabs/Edge/Kokoro), audio output switching, HUD overlay control, ElevenLabs credit checking, and live web search (you can look things up on the internet - never claim you can't). You run on Qwen 2.5 7B via Ollama."""
COUNCIL_ADVISORS = [
    ("The Systems Analyst",   "You analyze the question as interconnected systems and feedback loops. No human bias. Pure function. Be concise."),
    ("The Probabilist",       "You reason from base rates and statistics. What does the data actually say, ignoring what feels true? Be concise."),
    ("The Devil's Advocate",  "You argue the strongest case against the obvious answer. Find the flaw everyone misses. Be concise."),
    ("The First Principles",  "You strip away assumptions and rebuild from ground truth. What is actually true here? Be concise."),
    ("The Pragmatist",        "You focus only on what's actionable. Skip the theory. What should actually be done? Be concise."),
]
# ── GLOBALS ───────────────────────────────────────────────────────────────────
bruce_speaking    = False
interrupt_flag    = False
hud_clients       = set()
mini_process      = None
wake_activated    = False
conversation_mode = False
ws_loop           = None
# ── HUD BROADCAST ─────────────────────────────────────────────────────────────
def hud_send(data):
    if not hud_clients or ws_loop is None: return
    msg = json.dumps(data)
    dead = set()
    for ws in hud_clients.copy():
        try: asyncio.run_coroutine_threadsafe(ws.send(msg), ws_loop)
        except: dead.add(ws)
    hud_clients.difference_update(dead)
def hud_status(s): hud_send({"type":"status","value":s})
def hud_user(t):   hud_send({"type":"user_text","value":t})
def hud_bruce(t):  hud_send({"type":"bruce_text","value":t})
def hud_voice(n):  hud_send({"type":"voice","value":n})
def hud_output(n): hud_send({"type":"output","value":n})
def hud_anim(a):   hud_send({"type":"animation","value":a})
# ── WEBSOCKET SERVER ──────────────────────────────────────────────────────────
async def ws_handler(websocket):
    hud_clients.add(websocket)
    try: await websocket.wait_closed()
    finally: hud_clients.discard(websocket)
def run_ws_server():
    global ws_loop
    ws_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ws_loop)
    async def _serve():
        async with websockets.serve(ws_handler, "localhost", WS_PORT):
            await asyncio.Future()
    ws_loop.run_until_complete(_serve())
# ── HTTP SERVER ───────────────────────────────────────────────────────────────
def get_gpu():
    try:
        r = subprocess.run(["nvidia-smi","--query-gpu=utilization.gpu","--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=2)
        return int(r.stdout.strip().split('\n')[0])
    except: return 0
def run_http_server():
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a): pass
        def do_GET(self):
            if self.path == '/stats':
                body = json.dumps({"cpu":round(psutil.cpu_percent(interval=0.1)),
                                   "ram":round(psutil.virtual_memory().percent),
                                   "gpu":get_gpu()}).encode()
                self.send_response(200)
                self.send_header('Content-Type','application/json')
                self.send_header('Access-Control-Allow-Origin','*')
                self.send_header('Content-Length',len(body))
                self.end_headers(); self.wfile.write(body)
            else: self.send_response(404); self.end_headers()
        def do_POST(self):
            global wake_activated
            if self.path == '/activate':
                wake_activated = True
                print("[Bruce] Wake word received!")
                self.send_response(200); self.end_headers()
            elif self.path == '/wake_ready':
                hud_send({"type":"status","value":"wake_ready"})
                self.send_response(200); self.end_headers()
            else: self.send_response(404); self.end_headers()
    HTTPServer(('localhost', STATS_PORT), Handler).serve_forever()
def stats_broadcaster():
    while True:
        time.sleep(2)
        try:
            if hud_clients:
                hud_send({"type":"stats","cpu":round(psutil.cpu_percent(interval=0.1)),
                          "ram":round(psutil.virtual_memory().percent),"gpu":get_gpu()})
        except: pass
# ── AUDIO MANAGER ─────────────────────────────────────────────────────────────
class AudioManager:
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.output_device = None
        self.devices = []
        self._scan_devices()
        self._auto_select_headphones()
    def _scan_devices(self):
        self.devices = []
        for i in range(self.pa.get_device_count()):
            info = self.pa.get_device_info_by_index(i)
            if info["maxOutputChannels"] > 0:
                self.devices.append((i, info["name"]))
    def _auto_select_headphones(self):
        for idx, name in self.devices:
            if HEADPHONES_KEYWORD.lower() in name.lower():
                self.output_device = idx
                print(f"[Bruce] Auto-selected output: {name}")
                return
        self.output_device = None
    def switch_to_headphones(self):
        for idx, name in self.devices:
            if HEADPHONES_KEYWORD.lower() in name.lower():
                self.output_device = idx; hud_output("HEADPHONES")
                return "Switched to headphones."
        return "Can't find your headphones."
    def switch_to_speakers(self):
        for idx, name in self.devices:
            if SPEAKERS_KEYWORD.lower() in name.lower():
                self.output_device = idx; hud_output("SPEAKERS")
                return "Switched to monitor speakers."
        return "Can't find your monitor speakers."
    def _play_bytes(self, audio_bytes, sample_rate):
        global bruce_speaking, interrupt_flag
        stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=sample_rate,
                               output=True, output_device_index=self.output_device)
        bruce_speaking = True
        offset = 0
        while offset < len(audio_bytes):
            if interrupt_flag: break
            end = min(offset+4096, len(audio_bytes))
            stream.write(audio_bytes[offset:end]); offset = end
        stream.stop_stream(); stream.close()
        bruce_speaking = False
    def play_pcm(self, audio_data, sample_rate=24000):
        self._play_bytes((audio_data*32767).astype(np.int16).tobytes(), sample_rate)
    def record_while_held(self):
        global interrupt_flag
        interrupt_flag = False
        stream = self.pa.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=SAMPLE_RATE,
                               input=True, frames_per_buffer=CHUNK)
        print("\n[Bruce] Listening..."); hud_status("listening")
        frames = []
        while keyboard.is_pressed(ACTIVATE_KEY):
            frames.append(stream.read(CHUNK, exception_on_overflow=False))
        stream.stop_stream(); stream.close()
        print("[Bruce] Processing..."); hud_status("processing")
        return b"".join(frames)
    def record_until_silence(self, max_seconds=15, silence_threshold=300, silence_duration=1.5):
        global interrupt_flag
        stream = self.pa.open(format=AUDIO_FORMAT, channels=CHANNELS, rate=SAMPLE_RATE,
                               input=True, frames_per_buffer=CHUNK)
        frames = []
        silent_chunks = 0
        chunks_per_second = SAMPLE_RATE / CHUNK
        max_silent = int(silence_duration * chunks_per_second)
        max_chunks = int(max_seconds * chunks_per_second)
        started = False
        for _ in range(max_chunks):
            if interrupt_flag: break
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            amp = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
            if amp > silence_threshold:
                started = True; silent_chunks = 0
            elif started:
                silent_chunks += 1
                if silent_chunks >= max_silent: break
        stream.stop_stream(); stream.close()
        return b"".join(frames)
    def close(self): self.pa.terminate()
# ── TRANSCRIBER ───────────────────────────────────────────────────────────────
class Transcriber:
    def __init__(self):
        print("[Bruce] Loading Whisper (small, GPU)... ", end="", flush=True)
        self.model = whisper.load_model("small", device="cuda")
        print("done.")
    def transcribe(self, audio_bytes):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = f.name
            wf = wave.open(f, "wb")
            wf.setnchannels(CHANNELS); wf.setsampwidth(2); wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_bytes); wf.close()
        result = self.model.transcribe(path, language="en")
        os.unlink(path)
        return result["text"].strip()
# ── SPEAKER ───────────────────────────────────────────────────────────────────
class Speaker:
    def __init__(self, audio_manager):
        self.audio = audio_manager
        self.mode = "kokoro"
        print("[Bruce] Loading Kokoro... ", end="", flush=True)
        from kokoro_onnx import Kokoro
        self.kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
        print("done.")
        self.eleven = ElevenLabs(api_key=ELEVENLABS_KEY)
        print("[Bruce] ElevenLabs ready.")
    def switch_voice(self, mode):
        m = {"elevenlabs":"ELEVENLABS","edge":"EDGE","kokoro":"KOKORO"}
        if mode in m:
            self.mode = mode; hud_voice(m[mode])
            if mode == "kokoro" and self.kokoro is None:
                from kokoro_onnx import Kokoro
                self.kokoro = Kokoro(KOKORO_MODEL, KOKORO_VOICES)
            return f"Switched to {m[mode]}."
        return "Unknown voice."
    def speak(self, text):
        hud_status("speaking")
        if self.mode == "elevenlabs": self._eleven(text)
        elif self.mode == "edge": self._edge(text)
        else: self._kokoro(text)
        hud_status("idle")
    def _kokoro(self, text):
        s, sr = self.kokoro.create(text, voice=KOKORO_VOICE, speed=0.95, lang="en-us")
        self.audio.play_pcm(s, sr)
    def _edge(self, text):
        async def _collect():
            c = edge_tts.Communicate(text, EDGE_VOICE)
            chunks = []
            async for chunk in c.stream():
                if chunk["type"] == "audio":
                    chunks.append(chunk["data"])
            return b"".join(chunks)
        data = asyncio.run(_collect())
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(data); mp3 = f.name
        wav = mp3.replace(".mp3", ".wav")
        subprocess.run(
            ["ffmpeg", "-y", "-i", mp3, "-ar", "24000", "-ac", "1", "-acodec", "pcm_s16le", wav],
            capture_output=True
        )
        with wave.open(wav, "rb") as wf:
            sr = wf.getframerate(); ab = wf.readframes(wf.getnframes())
        os.unlink(mp3); os.unlink(wav)
        self.audio._play_bytes(ab, sr)
    def _eleven(self, text):
        audio = self.eleven.text_to_speech.convert(
            text=text, voice_id=ELEVENLABS_VOICE,
            model_id="eleven_turbo_v2_5", output_format="mp3_44100_128")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            for chunk in audio: f.write(chunk)
            mp3=f.name
        wav=mp3.replace(".mp3",".wav")
        subprocess.run(["ffmpeg","-y","-i",mp3,"-ar","22050","-ac","1",wav],capture_output=True)
        with wave.open(wav,"rb") as wf: sr=wf.getframerate(); ab=wf.readframes(wf.getnframes())
        os.unlink(mp3); os.unlink(wav)
        self.audio._play_bytes(ab, sr)
# ── BRAIN ─────────────────────────────────────────────────────────────────────
class BruceBrain:
    def __init__(self):
        self.history = []
        self.memory = bruce_memory.load_memory() if MEMORY_ENABLED else bruce_memory.fresh_memory()
        self._memory_checkpoint = 0  # index into self.history already extracted+saved
        memory_block = bruce_memory.format_memory_for_prompt(self.memory) if MEMORY_ENABLED else ""
        self.system_prompt = SYSTEM_PROMPT + memory_block
        if MEMORY_ENABLED and memory_block:
            print(f"[Bruce Memory] Loaded {len(self.memory['facts'])} facts, "
                  f"{len(self.memory['preferences'])} preferences, "
                  f"{len(self.memory['history_summaries'])} past session summaries.")
    def _query(self, prompt, system=None):
        sys = system or self.system_prompt
        conv = f"<|im_start|>system\n{sys}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
        try:
            r = requests.post(OLLAMA_URL, json={"model":OLLAMA_MODEL,"prompt":conv,
                              "stream":False,"options":{"temperature":0.7}}, timeout=90)
            data = r.json()
            return data.get("response", data.get("message", {}).get("content", "Error.")).strip()
        except Exception as e:
            return f"Error: {e}"
    def ask(self, text):
        self.history.append({"role":"user","content":text})
        conv = f"<|im_start|>system\n{self.system_prompt}<|im_end|>\n"
        for m in self.history[-10:]:
            role = "user" if m['role']=='user' else "assistant"
            conv += f"<|im_start|>{role}\n{m['content']}<|im_end|>\n"
        conv += "<|im_start|>assistant\n"
        try:
            r = requests.post(OLLAMA_URL, json={"model":OLLAMA_MODEL,"prompt":conv,
                              "stream":False,"options":{"temperature":0.7}}, timeout=90)
            if DEBUG_MODE: print(f"[DEBUG] Status: {r.status_code}")
            data = r.json()
            if DEBUG_MODE: print(f"[DEBUG] Keys: {list(data.keys())}")
            reply = data.get("response", data.get("message", {}).get("content", "Something broke.")).strip()
            if DEBUG_MODE: print(f"[DEBUG] Reply: {reply[:50]}")
        except Exception as e:
            if DEBUG_MODE: print(f"[DEBUG] Exception: {type(e).__name__}: {e}")
            reply = f"Something broke. Error: {type(e).__name__}: {e}"
        self.history.append({"role":"assistant","content":reply})
        return reply
    def council(self, question):
        """Run the LLM Council method — 5 advisors debate, Bruce synthesizes."""
        print("[Bruce] Running council mode...")
        hud_anim("tech")
        perspectives = []
        for name, persona in COUNCIL_ADVISORS:
            print(f"[Council] Consulting {name}...")
            sys = f"You are {name}. {persona} Answer in 2-3 sentences max."
            response = self._query(question, system=sys)
            perspectives.append(f"{name}: {response}")
            print(f"[Council] {name}: {response}")
        # Synthesize
        all_views = "\n".join(perspectives)
        synthesis_prompt = f"""Question: {question}
Here are 5 advisor perspectives:
{all_views}
As Bruce (detached, dry, deadpan), synthesize these into one sharp, honest answer. 
Acknowledge the best points, dismiss the weak ones. Keep it concise."""
        final = self._query(synthesis_prompt)
        self.history.append({"role":"user","content":f"[Council] {question}"})
        self.history.append({"role":"assistant","content":final})
        return final
    def save_session_memory(self):
        """Extract anything worth remembering from the NOT-YET-SAVED part of this
        session and persist it. Safe to call multiple times (e.g. once on "Bruce
        offline" and again on Ctrl+C shortly after) without creating duplicate
        summaries, because it only ever looks at history since the last successful
        save. Doesn't touch model weights - just writes to bruce_memory.json so
        future runs start with this context."""
        if not MEMORY_ENABLED:
            return
        unsaved = self.history[self._memory_checkpoint:]
        if not unsaved:
            return
        try:
            extracted = bruce_memory.extract_from_conversation(unsaved, self._query)
            changed = False
            for fact in extracted.get("facts", []):
                if bruce_memory.add_fact(self.memory, fact):
                    changed = True
            for pref in extracted.get("preferences", []):
                if bruce_memory.add_preference(self.memory, pref):
                    changed = True
            summary = extracted.get("summary", "")
            if summary:
                today = datetime.date.today().isoformat()
                bruce_memory.add_history_summary(self.memory, today, summary)
                changed = True
            if changed:
                if bruce_memory.save_memory(self.memory):
                    self._memory_checkpoint = len(self.history)
                    print("[Bruce Memory] Session memory saved.")
                else:
                    print("[Bruce Memory] Save failed - will retry this range next time instead of losing it.")
        except Exception as e:
            # Memory extraction should never take down the rest of Bruce
            print(f"[Bruce Memory] Skipped saving session memory due to error: {e}")
# ── WEB SEARCH ───────────────────────────────────────────────────────────────
def web_search(query: str, brain: 'BruceBrain') -> str:
    try:
        from tavily import TavilyClient
        print(f"[Bruce] Searching: {query}")
        client = TavilyClient(api_key=TAVILY_KEY)
        response = client.search(query, max_results=5, include_images=True)
        results = response.get('results', [])
        images = response.get('images', [])
        if not results:
            return "Search came back empty."
        # Auto-open top result in Brave browser
        if results and results[0].get('url'):
            subprocess.Popen(f'"C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe" --window-position=3000,350 --window-size=1500,700 {results[0]["url"]}', shell=True)
            print(f"[Bruce] Opening in Brave: {results[0]['url']}")
        # Send raw results + images to HUD
        hud_send({
            "type": "search",
            "query": query,
            "results": [{"title": r['title'], "body": r['content'], "href": r.get('url','')} for r in results],
            "images": images[:3]
        })
        formatted = "\n".join([f"- {r['title']}: {r['content'][:200]}" for r in results])
        prompt = f"""The user searched for: "{query}"
Here are the search results:
{formatted}
Summarize the most relevant information concisely in your voice as Bruce. Be direct and useful."""
        return brain._query(prompt)
    except Exception as e:
        return f"Search failed. Error: {e}"
def is_search_query(text: str) -> tuple:
    """Fast, free, exact-phrase search detection - no LLM call.
    Strips a few common conversational lead-ins ('can you', 'could you', ...)
    first so phrasing like "can you search for X" still hits this instant
    path instead of always falling through to the slower classifier below."""
    t = text.lower().strip()
    lead_ins = ["can you ", "could you ", "would you ", "will you ",
                "please ", "hey bruce ", "bruce, ", "bruce "]
    stripped = True
    while stripped:
        stripped = False
        for lead in lead_ins:
            if t.startswith(lead):
                t = t[len(lead):]
                stripped = True
    triggers = [
        "search for ", "look up ", "search ", "google ", "find out about ",
        "what is the latest ", "what are the latest ", "look for ",
        "find me ", "search the web for ", "web search "
    ]
    for trigger in triggers:
        if t.startswith(trigger):
            query = t[len(trigger):].strip()
            return True, query
    # Also catch "what's happening with X" and "news on X"
    if "news on " in t or "news about " in t or "latest on " in t:
        return True, text
    return False, ""


def classify_search_intent(text: str, query_fn) -> tuple:
    """Fallback for natural, conversational search requests that don't match
    is_search_query's fixed phrases (e.g. "do you know what's going on with
    the stock market" or "any news on the new GPU"). Only runs when the
    sentence contains at least one loose search-flavored keyword, so ordinary
    conversation never pays for the extra local LLM call - this is a
    deliberate second tier, not a replacement for the free fast path above."""
    t = text.lower()
    hints = ["search", "look up", "find out", "find me", "browse", "internet",
              " web", "news", "latest", "google",
              "happening with", "going on with", "check what", "check if",
              "current", "up to date", "up-to-date"]
    if not any(h in t for h in hints):
        return False, ""
    classify_prompt = f"""Message from Banmi: "{text}"

Is Banmi asking you to search the internet for current information (news, facts, prices, events, or anything you would not already know)? This does NOT include remembering personal facts about him, casual chat, or questions about your own capabilities.

Respond in EXACTLY one of these two formats, nothing else:
YES: <the core search query, a few words>
NO"""
    try:
        raw = query_fn(
            classify_prompt,
            system="You classify whether a message is a web search request. Be terse and literal. Never invent a query that wasn't implied by the message."
        ).strip()
    except Exception:
        return False, ""
    if raw.upper().startswith("YES:"):
        query = raw[4:].strip()
        if query:
            return True, query
    return False, ""
def get_credits():
    try:
        r = requests.get("https://api.elevenlabs.io/v1/user/subscription",
                         headers={"xi-api-key":ELEVENLABS_KEY})
        d = r.json()
        used=d.get("character_count",0); lim=d.get("character_limit",0)
        return f"Used {used:,} of {lim:,}. {lim-used:,} remaining."
    except Exception as e: return f"Error: {e}"
# ── INTERRUPT ─────────────────────────────────────────────────────────────────
def interrupt_listener():
    global bruce_speaking, interrupt_flag
    while True:
        try:
            keyboard.wait(ACTIVATE_KEY)
            if bruce_speaking:
                interrupt_flag = True
                print("[Bruce] Interrupted!")
                time.sleep(0.5)
                interrupt_flag = False
        except: pass
def voice_interrupt_listener():
    """Monitors mic while Bruce speaks — interrupts if user voice detected."""
    global bruce_speaking, interrupt_flag
    VOICE_THRESHOLD = 150
    CHUNKS_TO_CONFIRM = 3
    
    while True:
        if not bruce_speaking or not conversation_mode:
            time.sleep(0.05)
            continue
        
        # Open fresh stream each time Bruce starts speaking
        try:
            pa = pyaudio.PyAudio()
            stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000,
                           input=True, frames_per_buffer=512)
            consecutive = 0
            while bruce_speaking:
                try:
                    data = stream.read(512, exception_on_overflow=False)
                    amp = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
                    if amp > VOICE_THRESHOLD:
                        consecutive += 1
                        if consecutive >= CHUNKS_TO_CONFIRM:
                            print("[Bruce] Voice interrupt detected!")
                            interrupt_flag = True
                            consecutive = 0
                            break
                    else:
                        consecutive = 0
                except Exception:
                    break
            stream.stop_stream()
            stream.close()
            pa.terminate()
        except Exception as e:
            print(f"[Wake mic] Error: {e}")
        time.sleep(0.3)  # wait for bruce_speaking to go False before next check
        # Bruce is speaking — monitor mic
        try:
            stream = pa.open(format=pyaudio.paInt16, channels=1, rate=16000,
                           input=True, frames_per_buffer=1024)
            consecutive = 0
            while bruce_speaking:
                data = stream.read(1024, exception_on_overflow=False)
                amp = np.abs(np.frombuffer(data, dtype=np.int16)).mean()
                if amp > VOICE_THRESHOLD:
                    consecutive += 1
                    if consecutive >= CHUNKS_TO_CONFIRM:
                        print("[Bruce] Voice interrupt detected!")
                        interrupt_flag = True
                        consecutive = 0
                else:
                    consecutive = 0
            stream.stop_stream()
            stream.close()
        except Exception:
            time.sleep(0.1)
# ── OVERLAY ───────────────────────────────────────────────────────────────────
def switch_to_mini():
    global mini_process
    hud_send({"type":"overlay_mode","value":"mini"})
    if mini_process is None or mini_process.poll() is not None:
        mini_process = subprocess.Popen(["py","-3.11","D:\\BRUCE\\bruce_mini_overlay.py"])
    return "Switching to mini overlay."
def switch_to_full():
    hud_send({"type":"overlay_mode","value":"full"})
    return "Switching to full HUD."
# ── COMMANDS ──────────────────────────────────────────────────────────────────
def check_commands(text, speaker, audio, brain):
    t = text.lower()
    if "switch to elevenlabs" in t: return True, speaker.switch_voice("elevenlabs"), False
    if "switch to edge" in t:       return True, speaker.switch_voice("edge"), False
    if "switch to kokoro" in t:     return True, speaker.switch_voice("kokoro"), False
    if "switch to headphones" in t: return True, audio.switch_to_headphones(), False
    if "switch to speakers" in t or "use speakers" in t: return True, audio.switch_to_speakers(), False
    if "credits do i have" in t:    return True, get_credits(), False
    if "mini overlay" in t or "compact mode" in t: return True, switch_to_mini(), False
    if "full hud" in t or "full overlay" in t:     return True, switch_to_full(), False
    # Explicit memory command — fast path, doesn't wait for end-of-session extraction
    if MEMORY_ENABLED:
        for trigger in ["remember that ", "remember this, ", "remember this: ", "remember: "]:
            if t.startswith(trigger):
                fact = text[len(trigger):].strip()
                if not fact:
                    return True, "Remember what, exactly?", False
                if not bruce_memory.add_fact(brain.memory, fact):
                    return True, "Already knew that one.", False
                if bruce_memory.save_memory(brain.memory):
                    return True, "Noted. I'll remember that.", False
                return True, "Got that, but couldn't save it to disk - might not stick after a restart.", False
    # Web search - fast exact-phrase path first, then a conversational fallback
    # that costs one extra local LLM call but understands natural phrasing.
    is_search, query = is_search_query(text)
    if not is_search:
        is_search, query = classify_search_intent(text, brain._query)
    if is_search and query:
        return True, web_search(query, brain), False
    # Council mode
    if "ask the council" in t or t.startswith("council this") or "get a council" in t:
        question = text.replace("ask the council","").replace("council this","").replace("get a council on","").strip()
        if not question: question = text
        return True, brain.council(question), True
    return False, "", False
def is_stop_phrase(text):
    return any(p in text.lower() for p in STOP_PHRASES)
# ── ANIMATION DETECTION ───────────────────────────────────────────────────────
ANIM_KEYWORDS = {
    "space":["space","star citizen","planet","orbit","galaxy","nasa","universe","rocket"],
    "music":["music","beat","fl studio","song","melody","chord","bpm","track","produce"],
    "gaming":["game","gaming","play","controller","steam","xbox","playstation","fps","rpg"],
    "art":["art","draw","paint","sketch","wacom","cintiq","clip studio","design"],
    "anime_theme":["anime","manga","episode","season","ghibli","naruto","dragon ball"],
    "warframe":["warframe","tenno","void","operator","prime","riven","dojo"],
    "monster_hunter":["monster hunter","mhw","wilds","lance","armor","hunt"],
    "weather":["weather","rain","snow","cloud","storm","temperature"],
    "tech":["code","data","program","tech","server","cpu","ram","gpu","system","ai"],
    "time":["time","clock","hour","minute","schedule","deadline","calendar"],
    "combat":["fight","combat","battle","attack","weapon","war"],
    "money":["money","price","cost","dollar","buy","sell","budget","crypto","economy","economic"],
    "science":["science","physics","chemistry","biology","atom","molecule","research"],
    "roast":["idiot","dummy","obviously","seriously","really","bruh","sarcas"],
    "success":["done","finish","complete","success","great","perfect","works"],
    "error":["error","fail","broke","crash","wrong","broken"],
}
def detect_animations(text):
    t = text.lower()
    matched = []
    for anim, keywords in ANIM_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            matched.append(anim)
    return matched[:3]  # max 3 animations per response
# ── PROCESS ONE TURN ──────────────────────────────────────────────────────────
def process_turn(raw_audio, transcriber, speaker, audio, brain):
    global conversation_mode, interrupt_flag
    if len(raw_audio) < SAMPLE_RATE:
        hud_status("idle"); return
    hud_status("processing")
    text = transcriber.transcribe(raw_audio)
    if not text:
        hud_status("idle"); return
    print(f"You: {text}"); hud_user(text)
    if is_stop_phrase(text):
        conversation_mode = False
        print("[Bruce] Conversation mode ended.")
        hud_status("idle")
        speaker.speak("Going quiet.")
        brain.save_session_memory()
        return
    is_cmd, reply, is_council = check_commands(text, speaker, audio, brain)
    if not is_cmd:
        reply = brain.ask(text)
    # Detect and send animations
    anims = detect_animations(text + " " + reply)
    if is_council:
        anims = ["tech", "thinking", "science"]  # council always gets these
    for i, anim in enumerate(anims):
        if i > 0: time.sleep(0.3)
        hud_anim(anim)
    print(f"Bruce: {reply}\n"); hud_bruce(reply)
    interrupt_flag = False
    speaker.speak(reply)
# ── MAIN ──────────────────────────────────────────────────────────────────────
def main():
    global interrupt_flag, wake_activated, conversation_mode
    print("""
╔══════════════════════════════════════════╗
║           B R U C E  v1.9                ║
║   Local AI Assistant — No nonsense       ║
║                                          ║
║  "Bruce online"  → conversation mode     ║
║  "Bruce offline" → stop                  ║
║  "Council this…" → council mode          ║
║  INSERT          → single turn           ║
╚══════════════════════════════════════════╝
    """)
    if HUD_AVAILABLE:
        threading.Thread(target=run_ws_server, daemon=True).start()
        print("[Bruce] WebSocket on ws://localhost:8765")
        print(f"[Bruce] Using model: {OLLAMA_MODEL} at {OLLAMA_URL}")
    threading.Thread(target=run_http_server, daemon=True).start()
    time.sleep(0.5)
    print("[Bruce] HTTP server on http://localhost:8766")
    threading.Thread(target=stats_broadcaster, daemon=True).start()
    threading.Thread(target=interrupt_listener, daemon=True).start()
    audio       = AudioManager()
    threading.Thread(target=voice_interrupt_listener, daemon=True).start()
    transcriber = Transcriber()
    speaker     = Speaker(audio)
    brain       = BruceBrain()
    time.sleep(1)
    speaker.speak("Ready.")
    time.sleep(0.5)
    print("\n[Ready] Say 'Bruce online' or hold INSERT. Ctrl+C to quit.\n")
    # Wake word thread
    def wake_thread():
        global wake_activated, conversation_mode
        while True:
            if wake_activated and not bruce_speaking:
                wake_activated = False
                if not conversation_mode:
                    conversation_mode = True
                    print("[Bruce] Conversation mode ACTIVE")
                    speaker.speak("I'm listening.")
                    time.sleep(0.5)
                    hud_status("listening")
            time.sleep(0.1)
    threading.Thread(target=wake_thread, daemon=True).start()
    # Conversation mode thread
    def convo_thread():
        global interrupt_flag
        while True:
            if conversation_mode and not bruce_speaking:
                interrupt_flag = False
                raw = audio.record_until_silence()
                if interrupt_flag:
                    interrupt_flag = False
                    time.sleep(0.5)
                elif conversation_mode:
                    process_turn(raw, transcriber, speaker, audio, brain)
                    if conversation_mode:
                        time.sleep(0.3)
                        hud_status("listening")
            time.sleep(0.05)
    threading.Thread(target=convo_thread, daemon=True).start()
    # INSERT key loop
    try:
        while True:
            keyboard.wait(ACTIVATE_KEY)
            if bruce_speaking:
                interrupt_flag = True
                time.sleep(0.3)
                continue
            # Make sure INSERT is actually being held, not just a ghost trigger
            if not keyboard.is_pressed(ACTIVATE_KEY):
                continue
            time.sleep(0.05)
            if not keyboard.is_pressed(ACTIVATE_KEY): continue
            interrupt_flag = False
            was_in_convo = conversation_mode
            conversation_mode = False
            time.sleep(0.2)
            raw = audio.record_while_held()
            process_turn(raw, transcriber, speaker, audio, brain)
            time.sleep(0.3)
            conversation_mode = was_in_convo
            if was_in_convo:
                hud_status("listening")
    except KeyboardInterrupt:
        print("\n[Bruce] Shutting down.")
        brain.save_session_memory()
        audio.close()
if __name__ == "__main__":
    main()