import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.dashboard import DashboardService

def test_dashboard():
    dashboard = DashboardService()
    dashboard.start()

    try:
        # Simulate some state changes
        dashboard.update_state("Listening")
        time.sleep(2)

        dashboard.update_stt("show me the latest changes in the llama index service")
        dashboard.update_intent("file_search")
        time.sleep(2)

        dashboard.update_state("Thinking")
        dashboard.update_llm("Sure, here are the recent changes to the Llama Indexing Service:")
        time.sleep(2)

        dashboard.update_performance({"Startup": "2.57s", "LLM Response": "1.82s"})
        dashboard.update_audio_level(0.08, 0.15)
        time.sleep(2)

    except KeyboardInterrupt:
        pass
    finally:
        dashboard.stop()

if __name__ == "__main__":
    test_dashboard()

