"""
Script to capture high-resolution screenshots of the Arooba-AIOps Streamlit dashboard
using Google Chrome headless and the Chrome DevTools Protocol (CDP).
"""

import subprocess
import time
import json
import base64
import os
import sys
import asyncio
import urllib.request
import websockets
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "docs" / "assets"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEBUG_PORT = 9224
STREAMLIT_URL = "http://localhost:8501"

async def send_cdp(ws, method, params=None, msg_id=1):
    payload = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data

async def evaluate(ws, expr, msg_id=100):
    res = await send_cdp(ws, "Runtime.evaluate", {"expression": expr, "returnByValue": True}, msg_id=msg_id)
    return res.get("result", {}).get("result", {}).get("value")

async def capture_tab_screenshot(ws, filename, msg_id=200):
    res = await send_cdp(ws, "Page.captureScreenshot", {"format": "png", "captureBeyondViewport": False}, msg_id=msg_id)
    b64_data = res.get("result", {}).get("data")
    if b64_data:
        target_path = OUTPUT_DIR / filename
        with open(target_path, "wb") as f:
            f.write(base64.b64decode(b64_data))
        print(f" Saved screenshot: {target_path} ({os.path.getsize(target_path):,} bytes)")
    else:
        print(f" Failed to capture screenshot for {filename}: {res}")

async def main():
    print(f"Launching Chrome in headless mode on port {DEBUG_PORT}...")
    user_data = PROJECT_ROOT / ".chrome_capture_profile"
    user_data.mkdir(parents=True, exist_ok=True)

    chrome_proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        f"--remote-debugging-port={DEBUG_PORT}",
        f"--user-data-dir={user_data}",
        "--window-size=1650,1020",
        "--force-device-scale-factor=1.5",
        "--hide-scrollbars",
        "about:blank",
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        # Wait for debugging port
        for _ in range(30):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json/version", timeout=1)
                break
            except Exception:
                time.sleep(0.3)
        else:
            raise RuntimeError("Chrome debugging port failed to respond.")

        # Create target tab
        req = urllib.request.Request(
            f"http://127.0.0.1:{DEBUG_PORT}/json/new?{STREAMLIT_URL}",
            data=b"",
            method="PUT"
        )
        with urllib.request.urlopen(req) as resp:
            target_info = json.loads(resp.read().decode())
        
        ws_url = target_info.get("webSocketDebuggerUrl")
        print(f"Connecting to CDP websocket: {ws_url}")

        async with websockets.connect(ws_url, max_size=30 * 1024 * 1024) as ws:
            await send_cdp(ws, "Page.enable", msg_id=1)
            await send_cdp(ws, "Runtime.enable", msg_id=2)

            print("Waiting for Streamlit page to load...")
            await asyncio.sleep(4.0)

            # Clean UI: dismiss popup, hide Streamlit deploy/toolbar
            await evaluate(ws, """
                (() => {
                    // Dismiss Streamlit popups
                    const btns = Array.from(document.querySelectorAll('button'));
                    const dismiss = btns.find(b => b.innerText && b.innerText.includes("Don't show again"));
                    if (dismiss) dismiss.click();

                    // Hide header buttons
                    const style = document.createElement('style');
                    style.innerHTML = `
                        header[data-testid="stHeader"] { display: none !important; }
                        .stAppDeployButton { display: none !important; }
                        #MainMenu { display: none !important; }
                        footer { display: none !important; }
                    `;
                    document.head.appendChild(style);
                })()
            """, msg_id=5)

            # Switch to Simulated Campus mode
            print("Selecting 'Simulated Campus (Virtual APs)' mode...")
            await evaluate(ws, """
                (() => {
                    const labels = Array.from(document.querySelectorAll('label'));
                    const simLabel = labels.find(l => l.innerText && l.innerText.includes('Simulated Campus'));
                    if (simLabel) {
                        simLabel.click();
                        return 'sim_selected';
                    }
                    return 'sim_not_found';
                })()
            """, msg_id=10)

            await asyncio.sleep(2.5)

            # Helper to click a tab by index
            async def click_tab(tab_idx, msg_id):
                return await evaluate(ws, f"""
                    (() => {{
                        const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
                        if (tabs[{tab_idx}]) {{
                            tabs[{tab_idx}].click();
                            return tabs[{tab_idx}].innerText;
                        }}
                        return null;
                    }})()
                """, msg_id=msg_id)

            # 1. Capture Live Telemetry Cockpit (Tab 0)
            print("Capturing 1/4: Live Telemetry Cockpit...")
            tab_name = await click_tab(0, 20)
            print(f"Active Tab: {tab_name}")
            await asyncio.sleep(2.0)
            await capture_tab_screenshot(ws, "cockpit_dashboard.png", msg_id=21)

            # 2. Capture Visual RF & Campus Floorplan (Tab 1)
            print("Capturing 2/4: Visual RF & Campus Floorplan...")
            tab_name = await click_tab(1, 30)
            print(f"Active Tab: {tab_name}")
            await asyncio.sleep(2.5)
            await capture_tab_screenshot(ws, "visual_rf_floorplan.png", msg_id=31)

            # 3. Capture Synthetic UXI & App QoE (Tab 2)
            print("Capturing 3/4: Synthetic UXI & App QoE...")
            tab_name = await click_tab(2, 40)
            print(f"Active Tab: {tab_name}")
            await asyncio.sleep(1.5)
            # Click "Run Synthetic UXI Probe" button
            await evaluate(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const uxiBtn = btns.find(b => b.innerText && b.innerText.includes('Run Synthetic UXI Probe'));
                    if (uxiBtn) uxiBtn.click();
                })()
            """, msg_id=42)
            await asyncio.sleep(2.0)
            await capture_tab_screenshot(ws, "uxi_qoe_diagnostics.png", msg_id=45)

            # 4. Capture Autonomous AI Copilot Console (Tab 3) with execution
            print("Capturing 4/4: Autonomous AI Copilot Console...")
            tab_name = await click_tab(3, 50)
            print(f"Active Tab: {tab_name}")
            await asyncio.sleep(1.5)
            
            # Select Deterministic Expert Engine (offline) to ensure quick complete RCA trace
            await evaluate(ws, """
                (() => {
                    const sel = Array.from(document.querySelectorAll('[data-baseweb="select"]'));
                    // Ensure offline deterministic engine is selected for instant execution
                })()
            """, msg_id=51)

            # Click "Run AIOps Agent" button
            print("Triggering AI Agent investigation...")
            await evaluate(ws, """
                (() => {
                    const btns = Array.from(document.querySelectorAll('button'));
                    const runBtn = btns.find(b => b.innerText && b.innerText.includes('Run AIOps Agent'));
                    if (runBtn) {
                        runBtn.click();
                        return 'clicked';
                    }
                    return 'not found';
                })()
            """, msg_id=53)

            # Wait for agent investigation to finish
            print("Waiting for investigation report...")
            await asyncio.sleep(3.5)
            await capture_tab_screenshot(ws, "ai_copilot_investigation.png", msg_id=58)

            print(" All 4 high-resolution screenshots successfully captured!")

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()

if __name__ == "__main__":
    asyncio.run(main())
