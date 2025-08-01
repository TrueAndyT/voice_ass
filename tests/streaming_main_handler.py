#!/usr/bin/env python3
"""
Updated main handler with streaming LLM integration for minimal latency TTS.
This demonstrates how to integrate streaming responses into your existing voice assistant.
"""

import time
from services.llm_streaming_client import StreamingLLMClient, StreamingTTSIntegration
from services.logger import app_logger


def handle_wake_word_interaction_streaming(stt_service, streaming_llm_client, tts_service, log):
    """
    Enhanced wake word interaction handler with streaming LLM responses.
    This replaces the original handler in main.py for streaming functionality.
    """
    try:
        log.info("Starting transcription after wake word detection")
        
        # Record audio for transcription (same as before)
        from main import audio_stream_manager, record_audio_for_transcription
        import pyaudio
        
        with audio_stream_manager(
            pyaudio.paInt16, 1, 16000, int(16000 * 0.03)  # 30ms frames
        ) as stream:
            audio_data = record_audio_for_transcription(stream, timeout_ms=3000, log=log)
        
        if not audio_data:
            log.warning("No audio data recorded")
            return
        
        transcription = stt_service.transcribe_audio_bytes(audio_data)
        
        if not transcription:
            log.warning("STT service returned no transcription")
            return
        
        speech_end_time = time.time()
        log.info(f"Transcription received: {transcription}")
        
        # Start streaming LLM response with immediate TTS
        tts_start_time = time.time()
        log.info(f"LLM Query: {transcription}")
        
        # Create streaming integration
        integration = StreamingTTSIntegration(streaming_llm_client, tts_service, min_chunk_size=100)
        
        # This will start TTS as soon as first chunks are available
        complete_response = integration.speak_streaming_response(
            transcription,
            chunk_callback=lambda chunk: log.debug(f"TTS chunk: {len(chunk)} chars")
        )
        
        # Log performance metrics
        speech_to_tts_time = tts_start_time - speech_end_time
        log.info(f"Speech→TTS latency: {speech_to_tts_time:.2f}s")
        log.info(f"Complete response: {len(complete_response)} characters")
        
        # Handle follow-up conversation with streaming
        handle_followup_conversation_streaming(stt_service, streaming_llm_client, tts_service, log)
        
        log.info("Conversation ended - listening for wake word again")
        
    except Exception as e:
        log.error(f"Error during streaming wake word interaction: {e}", exc_info=True)


def handle_followup_conversation_streaming(stt_service, streaming_llm_client, tts_service, log):
    """Enhanced follow-up conversation handler with streaming."""
    integration = StreamingTTSIntegration(streaming_llm_client, tts_service, min_chunk_size=80)
    
    while True:
        try:
            log.debug("Listening for follow-up...")
            
            # Record audio for follow-up transcription (same as before)
            from main import audio_stream_manager, record_audio_for_transcription
            import pyaudio
            
            with audio_stream_manager(
                pyaudio.paInt16, 1, 16000, int(16000 * 0.03)  # 30ms frames
            ) as stream:
                audio_data = record_audio_for_transcription(stream, timeout_ms=4000, log=log)
            
            if not audio_data:
                log.info("Dialog ended due to inactivity")
                break
                
            follow_up = stt_service.transcribe_audio_bytes(audio_data)
            
            if not follow_up:
                log.info("Dialog ended due to inactivity")
                break
                
            log.info(f"Follow-up transcription: {follow_up}")
            
            # Stream response immediately to TTS
            complete_response = integration.speak_streaming_response(follow_up)
            log.info(f"Follow-up response: {len(complete_response)} characters")
            
        except Exception as e:
            log.error(f"Error during streaming follow-up conversation: {e}", exc_info=True)
            break


def create_streaming_voice_assistant():
    """
    Factory function to create a streaming-enabled voice assistant.
    This can replace parts of your main() function.
    """
    log = app_logger.get_logger("streaming_voice_assistant")
    
    try:
        # Load services (keeping existing microservices architecture)
        from services.microservices_loader import load_services_microservices
        
        log.info("Loading services with streaming LLM...")
        vad, oww_model, stt_service, _, tts_service, dynamic_rms, service_manager = load_services_microservices()
        
        # Replace LLM service with streaming client
        streaming_llm_client = StreamingLLMClient(port=8003)
        
        # Test streaming connection
        if streaming_llm_client.health_check():
            log.info("✅ Streaming LLM service is ready")
        else:
            log.warning("❌ Streaming LLM service not available, falling back to regular client")
            # Fallback to regular LLM client
            from services.llm_client import LLMClient
            streaming_llm_client = LLMClient(port=8003)
        
        return {
            'vad': vad,
            'oww_model': oww_model,
            'stt_service': stt_service,
            'streaming_llm_client': streaming_llm_client,
            'tts_service': tts_service,
            'dynamic_rms': dynamic_rms,
            'service_manager': service_manager
        }
        
    except Exception as e:
        log.error(f"Failed to create streaming voice assistant: {e}")
        raise


def demo_streaming_integration():
    """
    Demonstration of streaming LLM to TTS integration.
    Run this to test the streaming functionality.
    """
    print("🚀 Streaming LLM-to-TTS Integration Demo")
    print("=" * 50)
    
    log = app_logger.get_logger("streaming_demo")
    
    try:
        # Create streaming client and TTS service
        from services.llm_streaming_client import create_streaming_integration
        llm_client, tts_service, integration = create_streaming_integration()
        
        # Test prompts
        test_prompts = [
            "Tell me a joke about computers",
            "Explain how streaming works in simple terms",
            "What are the benefits of real-time AI responses?"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n🎯 Test {i}: {prompt}")
            print("-" * 40)
            
            start_time = time.time()
            
            # This will stream LLM response directly to TTS
            response = integration.speak_streaming_response(
                prompt,
                chunk_callback=lambda chunk: print(f"📢 TTS Chunk: {len(chunk)} chars")
            )
            
            total_time = time.time() - start_time
            print(f"✅ Complete! Total time: {total_time:.2f}s")
            print(f"📝 Response length: {len(response)} characters")
            
            # Short pause between tests
            time.sleep(2)
        
        print(f"\n🎉 Demo completed successfully!")
        
    except Exception as e:
        log.error(f"Demo failed: {e}")
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    # Run the demo
    demo_streaming_integration()
