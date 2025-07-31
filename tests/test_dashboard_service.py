import pytest
import time
import sys
import threading
from unittest.mock import patch, MagicMock
from services.dashboard import DashboardService, get_service_pids

class TestDashboardService:
    def generate_test_data_sets(self):
        """Generate 10 sets of test data for each component"""
        # 10 variations of each data type
        test_states = ["Initializing", "Listening", "Recording", "Processing", "Thinking", "Speaking", "Error", "Idle", "Busy", "Ready"]
        test_intents = ["N/A", "weather_query", "time_query", "music_request", "system_command", "general_question", "greeting", "goodbye", "help_request", "unknown"]
        test_audio_levels = [
            (0.00, 0.20), (0.05, 0.25), (0.12, 0.30), (0.18, 0.35), (0.25, 0.40),
            (0.32, 0.45), (0.28, 0.50), (0.15, 0.25), (0.45, 0.55), (0.38, 0.48)
        ]
        test_stt_outputs = [
            "What's the weather today?", "Set a timer for 5 minutes", "Play some music",
            "Turn off the lights", "What time is it?", "How are you doing?",
            "Tell me a joke", "What's on my calendar?", "Send a message", "Good morning"
        ]
        test_llm_outputs = [
            "Today's weather is sunny with a high of 75°F.", "Timer set for 5 minutes.",
            "Playing your favorite playlist now.", "I've turned off the lights for you.",
            "It's currently 3:45 PM.", "I'm doing well, thank you for asking!",
            "Why don't scientists trust atoms? Because they make up everything!",
            "You have a meeting at 4 PM today.", "Message sent successfully.",
            "Good morning! How can I help you today?"
        ]
        
        # 10 variations of performance metrics
        perf_metrics_sets = [
            {"LLM Response": "1.23s", "Tokens/sec": "15.2", "First Token": "0.25s", "Output Tokens": "42", "Input Tokens": "8", "Speech→TTS": "0.95s"},
            {"LLM Response": "2.45s", "Tokens/sec": "12.8", "First Token": "0.31s", "Output Tokens": "65", "Input Tokens": "12", "Speech→TTS": "1.15s"},
            {"LLM Response": "0.89s", "Tokens/sec": "18.7", "First Token": "0.18s", "Output Tokens": "28", "Input Tokens": "6", "Speech→TTS": "0.72s"},
            {"LLM Response": "3.12s", "Tokens/sec": "9.3", "First Token": "0.45s", "Output Tokens": "89", "Input Tokens": "15", "Speech→TTS": "1.38s"},
            {"LLM Response": "1.67s", "Tokens/sec": "14.1", "First Token": "0.28s", "Output Tokens": "51", "Input Tokens": "9", "Speech→TTS": "1.02s"},
            {"LLM Response": "2.01s", "Tokens/sec": "11.6", "First Token": "0.35s", "Output Tokens": "73", "Input Tokens": "13", "Speech→TTS": "1.25s"},
            {"LLM Response": "0.76s", "Tokens/sec": "21.4", "First Token": "0.15s", "Output Tokens": "19", "Input Tokens": "4", "Speech→TTS": "0.58s"},
            {"LLM Response": "2.89s", "Tokens/sec": "10.7", "First Token": "0.42s", "Output Tokens": "96", "Input Tokens": "18", "Speech→TTS": "1.45s"},
            {"LLM Response": "1.34s", "Tokens/sec": "16.8", "First Token": "0.22s", "Output Tokens": "38", "Input Tokens": "7", "Speech→TTS": "0.83s"},
            {"LLM Response": "2.56s", "Tokens/sec": "13.5", "First Token": "0.33s", "Output Tokens": "67", "Input Tokens": "11", "Speech→TTS": "1.18s"}
        ]
        
        # 10 variations of system resources for each service
        system_resources_sets = [
            {"App": {"cpu": 8.5, "ram": 485}, "Whisper": {"cpu": 25.3, "ram": 956, "gpu": 45, "vram": 234}, "Kokoro": {"cpu": 32.1, "ram": 1432, "gpu": 52, "vram": 467}, "Ollama": {"cpu": 18.7, "ram": 1876, "gpu": 68, "vram": 923}},
            {"App": {"cpu": 12.1, "ram": 523}, "Whisper": {"cpu": 28.9, "ram": 1087, "gpu": 58, "vram": 278}, "Kokoro": {"cpu": 41.5, "ram": 1598, "gpu": 63, "vram": 534}, "Ollama": {"cpu": 22.3, "ram": 2134, "gpu": 74, "vram": 1087}},
            {"App": {"cpu": 6.8, "ram": 467}, "Whisper": {"cpu": 19.2, "ram": 823, "gpu": 38, "vram": 189}, "Kokoro": {"cpu": 27.6, "ram": 1256, "gpu": 44, "vram": 398}, "Ollama": {"cpu": 15.1, "ram": 1645, "gpu": 59, "vram": 756}},
            {"App": {"cpu": 15.3, "ram": 578}, "Whisper": {"cpu": 35.7, "ram": 1245, "gpu": 67, "vram": 325}, "Kokoro": {"cpu": 48.2, "ram": 1789, "gpu": 71, "vram": 612}, "Ollama": {"cpu": 26.8, "ram": 2367, "gpu": 82, "vram": 1234}},
            {"App": {"cpu": 9.7, "ram": 501}, "Whisper": {"cpu": 22.4, "ram": 934, "gpu": 41, "vram": 223}, "Kokoro": {"cpu": 34.8, "ram": 1389, "gpu": 49, "vram": 445}, "Ollama": {"cpu": 19.5, "ram": 1923, "gpu": 64, "vram": 867}},
            {"App": {"cpu": 11.2, "ram": 534}, "Whisper": {"cpu": 31.6, "ram": 1156, "gpu": 62, "vram": 289}, "Kokoro": {"cpu": 39.4, "ram": 1523, "gpu": 58, "vram": 501}, "Ollama": {"cpu": 24.1, "ram": 2089, "gpu": 76, "vram": 1001}},
            {"App": {"cpu": 7.4, "ram": 478}, "Whisper": {"cpu": 17.8, "ram": 789, "gpu": 34, "vram": 167}, "Kokoro": {"cpu": 25.3, "ram": 1198, "gpu": 39, "vram": 356}, "Ollama": {"cpu": 13.6, "ram": 1567, "gpu": 55, "vram": 678}},
            {"App": {"cpu": 13.8, "ram": 556}, "Whisper": {"cpu": 33.2, "ram": 1298, "gpu": 69, "vram": 334}, "Kokoro": {"cpu": 45.7, "ram": 1656, "gpu": 73, "vram": 587}, "Ollama": {"cpu": 28.4, "ram": 2245, "gpu": 79, "vram": 1156}},
            {"App": {"cpu": 10.6, "ram": 512}, "Whisper": {"cpu": 26.1, "ram": 1023, "gpu": 48, "vram": 245}, "Kokoro": {"cpu": 36.9, "ram": 1467, "gpu": 54, "vram": 478}, "Ollama": {"cpu": 21.7, "ram": 1998, "gpu": 67, "vram": 934}},
            {"App": {"cpu": 14.5, "ram": 589}, "Whisper": {"cpu": 29.8, "ram": 1134, "gpu": 56, "vram": 267}, "Kokoro": {"cpu": 42.3, "ram": 1578, "gpu": 61, "vram": 523}, "Ollama": {"cpu": 25.9, "ram": 2156, "gpu": 71, "vram": 1078}}
        ]
        
        return test_states, test_intents, test_audio_levels, test_stt_outputs, test_llm_outputs, perf_metrics_sets, system_resources_sets

    @patch('services.dashboard.get_service_pids')
    @patch('services.dashboard.psutil.process_iter')
    @patch('services.dashboard.psutil.Process')
    @patch('services.dashboard.psutil.cpu_count')
    @patch('subprocess.run')
    def test_dashboard_live_display(self, mock_subprocess_run, mock_cpu_count, mock_psutil_process, mock_process_iter, mock_get_service_pids):
        """Test dashboard with live display for 30 seconds"""
        print("\n" + "="*60)
        print("STARTING DASHBOARD TEST - Will run for 30 seconds")
        print("Watch the dashboard update every second with different data")
        print("Console output simulation every 5 seconds")
        print("="*60)
        
        # Generate test data sets
        test_data = self.generate_test_data_sets()
        test_states, test_intents, test_audio_levels, test_stt_outputs, test_llm_outputs, perf_metrics_sets, system_resources_sets = test_data
        
        # Mock CPU count
        mock_cpu_count.return_value = 8
        
        # Mock GPU/VRAM data
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "72, 1145"
        
        # Mock service PIDs
        mock_get_service_pids.return_value = {"stt": 1001, "tts": 1002}
        
        # Mock ollama process search
        def mock_iter_processes(attrs):
            class MockOllamaProcess:
                def __init__(self):
                    self.info = {'pid': 1003, 'name': 'ollama'}
            return [MockOllamaProcess()]
        
        mock_process_iter.return_value = mock_iter_processes(['pid', 'name'])
        
        # Counter for cycling through data
        data_counter = 0
        
        # Mock process creation with dynamic data
        def create_mock_process(pid=None):
            current_resources = system_resources_sets[data_counter % 10]
            
            class MockProcess:
                def cpu_percent(self):
                    if pid is None:  # Main app
                        return current_resources["App"]["cpu"]
                    elif pid == 1001:  # Whisper
                        return current_resources["Whisper"]["cpu"]
                    elif pid == 1002:  # Kokoro
                        return current_resources["Kokoro"]["cpu"]
                    elif pid == 1003:  # Ollama
                        return current_resources["Ollama"]["cpu"]
                    return 0
                
                def memory_info(self):
                    class MemoryInfo:
                        def __init__(self, rss_mb):
                            self.rss = rss_mb * 1024 * 1024
                    
                    if pid is None:  # Main app
                        return MemoryInfo(current_resources["App"]["ram"])
                    elif pid == 1001:  # Whisper
                        return MemoryInfo(current_resources["Whisper"]["ram"])
                    elif pid == 1002:  # Kokoro
                        return MemoryInfo(current_resources["Kokoro"]["ram"])
                    elif pid == 1003:  # Ollama
                        return MemoryInfo(current_resources["Ollama"]["ram"])
                    return MemoryInfo(100)
            
            return MockProcess()
        
        mock_psutil_process.side_effect = create_mock_process
        
        # Initialize and start dashboard
        dashboard = DashboardService()
        dashboard.start()
        
        # Test loop
        start_time = time.time()
        console_output_counter = 0
        
        try:
            while time.time() - start_time < 30:
                # Update dashboard with current data set
                current_audio = test_audio_levels[data_counter % 10]
                
                dashboard.update_state(test_states[data_counter % 10])
                dashboard.update_intent(test_intents[data_counter % 10])
                dashboard.update_audio_level(current_audio[0], current_audio[1])
                dashboard.update_stt(test_stt_outputs[data_counter % 10])
                dashboard.update_llm(test_llm_outputs[data_counter % 10])
                dashboard.update_performance(perf_metrics_sets[data_counter % 10])
                
                # Simulate console output every 5 seconds
                if console_output_counter % 5 == 0:
                    # This will appear above the dashboard
                    sys.stdout.write(f"\r[CONSOLE] Simulated output #{console_output_counter//5 + 1} - Background process activity\n")
                    sys.stdout.flush()
                
                # Wait 1 second
                time.sleep(1)
                data_counter += 1
                console_output_counter += 1
                
        finally:
            dashboard.stop()
            print("\n" + "="*60)
            print("DASHBOARD TEST COMPLETED")
            print("Dashboard should have updated smoothly without flickering")
            print("All metrics and system resources should have been displayed")
            print("="*60)
            
        # Basic assertions to ensure test "passed"
        assert dashboard.assistant_state in test_states
        assert dashboard.intent in test_intents
        assert len(dashboard.perf_metrics) > 0
        
if __name__ == "__main__":
    test_instance = TestDashboardService()
    test_instance.test_dashboard_live_display()
