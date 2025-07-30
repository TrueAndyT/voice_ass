import torch
from services.tts_service import TTSService
import subprocess
import time
import threading

# Short sentence for basic test
short_text = "Hello, this is a test of the text-to-speech service."

# Long text with 10 varied sentences for buffering test
long_text = (
    "Welcome to the comprehensive text-to-speech stress testing system. "
    "This test is designed to evaluate the performance of the TTS service under various conditions. "
    "The system will process multiple sentences with different lengths and complexities. "
    "We are testing the chunking mechanism that breaks down long texts into manageable segments. "
    "The audio buffering system should maintain smooth playback without gaps or stuttering. "
    "Memory management is crucial when dealing with GPU-accelerated text-to-speech synthesis. "
    "The service must handle concurrent audio generation and playback threads efficiently. "
    "Error recovery mechanisms should activate if CUDA memory issues occur during processing. "
    "Quality assurance requires testing with realistic text content rather than simple repetitions. "
    "This final sentence completes our ten-sentence stress test for the TTS service evaluation."
)

# Function to fill GPU memory to simulate low VRAM availability
def simulate_vram_constraint(leave_free_gb=2):
    torch.cuda.empty_cache()
    total_memory = torch.cuda.get_device_properties(0).total_memory
    leave_free = leave_free_gb * (1024 ** 3)  # Bytes
    try:
        used_memory = total_memory - torch.cuda.memory_reserved(0)
        fill_memory = total_memory - used_memory - leave_free
        if fill_memory > 0:
            dummy_tensor = torch.zeros(int(fill_memory // 4), device="cuda")
            print(f"Simulated VRAM constraint: {fill_memory / (1024 ** 3):.2f} GB occupied.")
            return dummy_tensor  # Keep it allocated during the test
    except Exception as e:
        print(f"Failed to simulate VRAM constraint: {e}")


# Initialize TTS service
tts_service = TTSService()

# Run the VRAM constraint simulation
dummy_tensor = simulate_vram_constraint(1.5)  # Leave 1.5 GB free

# Start the TTS process
def run_tts_stress_test():
    try:
        print("Running TTS Stress Test...")
        start_time = time.time()

        # Warmup the pipeline
        tts_service.warmup()

        # VRAM Monitoring - runs every 5 seconds during TTS playback
        stop_monitoring = threading.Event()
        
        def monitor_vram_continuous():
            while not stop_monitoring.is_set():
                try:
                    allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)  # Convert bytes to GB
                    reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
                    total_memory = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                    usage_percent = (reserved / total_memory) * 100
                    print(f"VRAM - Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB ({usage_percent:.1f}% of {total_memory:.1f} GB)")
                except Exception as e:
                    print(f"VRAM Monitoring Error: {e}")
                
                # Wait 5 seconds or until stop signal
                if stop_monitoring.wait(5):
                    break

        # Start VRAM monitoring in background
        monitoring_thread = threading.Thread(target=monitor_vram_continuous)
        monitoring_thread.start()
        
        # Initial VRAM reading
        allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
        reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
        print(f"Initial VRAM - Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB")
        
        # Speak the long text
        tts_service.speak(long_text)
        
        # Stop monitoring and wait for thread to finish
        stop_monitoring.set()
        monitoring_thread.join()

        # Final VRAM reading
        allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)
        reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)
        print(f"Final VRAM - Allocated: {allocated:.2f} GB, Reserved: {reserved:.2f} GB")

        # Completion
        end_time = time.time()
        print(f"Stress test completed in {end_time - start_time:.2f} seconds.")

    except Exception as e:
        print(f"TTS Stress Test Error: {e}")

# Run the stress test
run_tts_stress_test()

# Cleanup VRAM constraint
if dummy_tensor is not None:
    del dummy_tensor
    torch.cuda.empty_cache()
    print("VRAM constraint released.")

