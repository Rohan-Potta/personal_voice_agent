#
# Personal HR-screening voice agent (Pipecat POC).
#
# Pipeline:  your voice  ->  Deepgram (STT)  ->  Groq/Llama (LLM brain)  ->  Cartesia (TTS)  ->  speaker
# Transport: WebRTC in the browser, so you can test it without any phone number.
#
# Run it:    python bot.py
# Then open the URL it prints (http://localhost:7860) and click Connect.
#

import os

from dotenv import load_dotenv
from loguru import logger

print("Starting screening voice agent...")
print("Loading models and imports (this takes ~20s the first time)\n")

logger.info("Loading Silero VAD model...")
from pipecat.audio.vad.silero import SileroVADAnalyzer

logger.info("✅ Silero VAD model loaded")

from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.transports.base_transport import BaseTransport, TransportParams

from persona import build_system_prompt

load_dotenv(override=True)

# Llama model served by Groq. Swap for another Groq-hosted model, or switch the whole
# service to Claude later (one import + one class change) if you want higher quality.
GROQ_MODEL = "llama-3.3-70b-versatile"

# Cartesia voice. Browse/preview voices at https://play.cartesia.ai and paste an ID here.
CARTESIA_VOICE = "71a7ad14-091c-4e8e-a314-022ece01c121"  # British Reading Lady


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting bot")

    stt = DeepgramSTTService(api_key=os.getenv("DEEPGRAM_API_KEY"))

    tts = CartesiaTTSService(
        api_key=os.getenv("CARTESIA_API_KEY"),
        settings=CartesiaTTSService.Settings(voice=CARTESIA_VOICE),
    )

    llm = GroqLLMService(
        api_key=os.getenv("GROQ_API_KEY"),
        settings=GroqLLMService.Settings(
            model=GROQ_MODEL,
            system_instruction=build_system_prompt(),
        ),
    )

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        [
            transport.input(),   # caller audio in
            stt,                 # speech -> text
            user_aggregator,     # track what the caller said
            llm,                 # Llama brain (knows about you)
            tts,                 # text -> speech
            transport.output(),  # agent audio out
            assistant_aggregator,  # track what the agent said
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(enable_metrics=True, enable_usage_metrics=True),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Caller connected")
        # Kick off the conversation with a screening-call greeting.
        context.add_message(
            {
                "role": "developer",
                "content": (
                    "Greet the caller warmly, introduce yourself as an AI assistant "
                    "that can answer questions about the person you represent, and ask "
                    "who's calling and how you can help."
                ),
            }
        )
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Caller disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Entry point used by Pipecat's dev runner."""
    transport_params = {
        "webrtc": lambda: TransportParams(audio_in_enabled=True, audio_out_enabled=True),
    }
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
