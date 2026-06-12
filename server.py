import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from twilio.twiml.voice_response import VoiceResponse, Connect
from bot import run_bot

app = FastAPI()

@app.post("/incoming-call")
async def incoming_call(request: Request):
    form_data = await request.form()
    call_sid = form_data.get("CallSid")
    
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=f"wss://{request.headers['host']}/ws/{call_sid}")
    response.append(connect)
    
    return HTMLResponse(content=str(response), media_type="application/xml")

@app.websocket("/ws/{call_sid}")
async def websocket_endpoint(websocket, call_sid: str):
    await websocket.accept()
    await run_bot(websocket)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
