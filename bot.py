import os
import json
import asyncio
from dotenv import load_dotenv
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.worker import PipelineWorker
from pipecat.processors.aggregators.llm_response_universal import (
    LLMUserAggregator,
    LLMAssistantAggregator,
    LLMContextFrame,
)
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.services.anthropic.llm import AnthropicLLMService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketTransport,
    FastAPIWebsocketParams,
)
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.serializers.twilio import TwilioFrameSerializer
from pipecat.serializers.base_serializer import FrameSerializer
from pipecat.frames.frames import Frame

load_dotenv()

SYSTEM_PROMPT = """Eres Sara, la asistente virtual de Servicios López, una empresa de servicios profesionales.
Tu misión es atender llamadas de clientes de forma amable, profesional y eficiente.

SERVICIOS QUE OFRECEMOS:
- Consultoría empresarial
- Gestión administrativa
- Soporte técnico básico
- Atención de incidencias

HORARIO: Lunes a viernes de 9:00 a 18:00. Sábados de 10:00 a 14:00.

INSTRUCCIONES:
- Saluda siempre con: "Buenos días/tardes, Servicios López, le atiende Sara. ¿En qué puedo ayudarle?"
- Habla siempre en español, de forma cercana pero profesional
- Si el cliente tiene una incidencia, recoge: nombre completo, teléfono de contacto y descripción del problema
- Si quiere información, responde con lo que sabes y ofrece que un especialista le llame
- Sé concisa — las respuestas en llamada deben ser cortas, máximo 2-3 frases
- Nunca inventes precios exactos, di que un especialista le confirmará el presupuesto
- Si no sabes algo, di: "Déjeme que lo consulte con el equipo y le llamamos en breve"
- Al despedirte confirma siempre los datos recogidos si los hay"""


class DynamicTwilioSerializer(FrameSerializer):

    def __init__(self):
        self._serializer = None
        self._stream_sid = None

    def set_stream_sid(self, stream_sid: str):
        self._stream_sid = stream_sid
        self._serializer = TwilioFrameSerializer(
            stream_sid=stream_sid,
            params=TwilioFrameSerializer.InputParams(auto_hang_up=False),
        )
        print(f"SERIALIZER ACTUALIZADO con stream_sid: {stream_sid}")

    async def serialize(self, frame: Frame) -> str | bytes | None:
        if self._serializer:
            return await self._serializer.serialize(frame)
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        if isinstance(data, str):
            try:
                msg = json.loads(data)
                print(f"DESERIALIZE EVENT: {msg.get('event')} | DATA: {data[:200]}")
                if msg.get("event") == "start" and not self._stream_sid:
                    stream_sid = msg["start"]["streamSid"]
                    self.set_stream_sid(stream_sid)
                    return await self._serializer.deserialize(data)
            except Exception as e:
                print(f"DESERIALIZE ERROR: {e}")
        if self._serializer:
            return await self._serializer.deserialize(data)
        return None


async def run_bot(websocket, call_sid: str):
    dynamic_serializer = DynamicTwilioSerializer()

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            vad_enabled=True,
            vad_analyzer=SileroVADAnalyzer(),
            vad_audio_passthrough=True,
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
            serializer=dynamic_serializer,
        ),
    )

    llm = AnthropicLLMService(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-sonnet-4-20250514",
    )

    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        language="es",
        model="nova-2",
    )

    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id=os.getenv("ELEVENLABS_VOICE_ID"),
        model="eleven_multilingual_v2",
    )

    context = LLMContext()
    context.set_messages([
        {"role": "user", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Entendido, estoy lista para atender llamadas."},
    ])

    user_aggregator = LLMUserAggregator(context)
    assistant_aggregator = LLMAssistantAggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    task = PipelineWorker(pipeline)

    @transport.event_handler("on_client_connected")
    async def on_connected(transport, client):
        for _ in range(50):
            if dynamic_serializer._stream_sid:
                break
            await asyncio.sleep(0.1)
        print(f"SALUDO con stream_sid: {dynamic_serializer._stream_sid}")
        await task.queue_frames([LLMContextFrame(context)])

    runner = PipelineRunner()
    await runner.run(task)
