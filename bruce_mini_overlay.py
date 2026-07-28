"""
Bruce Mini Overlay
Sits top-left corner, always on top
Like Discord's voice overlay
"""

import webview
import threading
import keyboard
import sys
import os
import asyncio
import websockets
import json

MINI_PATH = os.path.abspath("D:\\BRUCE\\BRUCE MINI.html")
TOGGLE_KEY = "end"

window = None
is_visible = True

def toggle_visibility():
    global is_visible
    if window is None: return
    try:
        is_visible = not is_visible
        if is_visible: window.show()
        else: window.hide()
    except Exception as e:
        print(f"[Mini] Toggle error: {e}")

def hotkey_listener():
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
                            if data['value'] == 'full':
                                if window: window.hide()
                            elif data['value'] == 'mini':
                                if window: window.show()
            except Exception:
                await asyncio.sleep(3)
    asyncio.run(listen())

def main():
    global window
    print("""
╔══════════════════════════════════════════╗
║      B R U C E  M I N I  v1.0           ║
║      Compact Corner Overlay              ║
║                                          ║
║  END — toggle visibility                 ║
╚══════════════════════════════════════════╝
    """)

    if not os.path.exists(MINI_PATH):
        print(f"[Mini] ERROR: {MINI_PATH} not found")
        sys.exit(1)

    threading.Thread(target=hotkey_listener, daemon=True).start()
    threading.Thread(target=check_overlay_messages, daemon=True).start()

    print("[Mini] Starting compact overlay at top-left...")

    window = webview.create_window(
        title="BRUCE MINI",
        url=f"file:///{MINI_PATH}",
        width=230,
        height=200,
        x=10,
        y=10,
        resizable=False,
        on_top=True,
        frameless=True,
        easy_drag=True,
        shadow=False,
    )

    webview.start(debug=False)

if __name__ == "__main__":
    main()
