import os
import json
import inspect
import uvicorn
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse
from twilio.twiml.voice_response import VoiceResponse, Connect
from pipecat.pipeline.task import PipelineTask
from bot import run_bot

print(inspect.signature(PipelineTask.__init__))
import pipecat.pipeline.worker as pw
import inspect
print(inspect.getsource(pw.PipelineWorker.__init__))
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
async def websocket_endpoint(websocket: WebSocket, call_sid: str):
    await websocket.accept()
    
    first_message = await websocket.receive_text()
    data = json.loads(first_message)
    stream_sid = data.get("streamSid", "")
    
    await run_bot(websocket, stream_sid)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
