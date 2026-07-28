"""
Bruce HUD Overlay Launcher
F11 - toggle borderless fullscreen
END - toggle visibility
"""

import webview
import threading
import keyboard
import sys
import os
import asyncio
import websockets
import json

HUD_PATH = os.path.abspath("D:\\BRUCE\\BRUCE __ SYSTEM HUD.html")
TOGGLE_KEY = "end"

window = None
is_fullscreen = False
is_visible = True

def toggle_visibility():
    global is_visible
    if window is None: return
    try:
        is_visible = not is_visible
        if is_visible: window.show()
        else: window.hide()
    except Exception as e:
        print(f"[Overlay] Toggle error: {e}")

def toggle_fullscreen():
    global is_fullscreen
    if window is None: return
    try:
        is_fullscreen = not is_fullscreen
        window.toggle_fullscreen()
    except Exception as e:
        print(f"[Overlay] Fullscreen error: {e}")

def hotkey_listener():
    keyboard.add_hotkey('f11', toggle_fullscreen)
    keyboard.add_hotkey(TOGGLE_KEY, toggle_visibility)
    keyboard.wait()

def check_overlay_messages():
    async def listen():
        while True:
            try:
                async with websockets.connect('ws://localhost:8765') as ws:
                    async for msg in ws:
                        data = json.loads(msg)
                        if data.get('type') == 'overlay_mode':
                            if data['value'] == 'mini':
                                if window: window.hide()
                            elif data['value'] == 'full':
                                if window: window.show()
            except Exception:
                await asyncio.sleep(3)
    asyncio.run(listen())

def main():
    global window
    print("""
╔══════════════════════════════════════════╗
║        B R U C E  H U D  v1.4           ║
║        Overlay Window                    ║
║                                          ║
║  END  — toggle HUD visibility            ║
║  F11  — toggle borderless fullscreen     ║
╚══════════════════════════════════════════╝
    """)

    if not os.path.exists(HUD_PATH):
        print(f"[Overlay] ERROR: HUD file not found at {HUD_PATH}")
        sys.exit(1)

    threading.Thread(target=hotkey_listener, daemon=True).start()
    threading.Thread(target=check_overlay_messages, daemon=True).start()

    print(f"[Overlay] Loading HUD...")

    window = webview.create_window(
        title="BRUCE HUD",
        url=f"file:///{HUD_PATH}",
        width=1200,
        height=700,
        resizable=True,
        on_top=True,
        frameless=False,
        easy_drag=True,
        shadow=True,
    )

    webview.start(debug=False)

if __name__ == "__main__":
    main()
