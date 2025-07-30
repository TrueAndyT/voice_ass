import pytest
from services.intent_detector import IntentDetector

class TestIntentDetector:
    def setup_method(self):
        """Setup IntentDetector for testing."""
        self.detector = IntentDetector()

    def test_memory_intent(self):
        """Test detection of memory intent."""
        assert self.detector.detect("remember to buy milk") == "memory"
        assert self.detector.detect("update memory with birthday") == "memory"
        assert self.detector.detect("remove memory about appointment") == "memory"
        assert self.detector.detect("list memories") == "memory"

    def test_file_search_intent(self):
        """Test detection of file search intent."""
        assert self.detector.detect("find the document") == "file_search"
        assert self.detector.detect("search for python files") == "file_search"
        assert self.detector.detect("locate config.json") == "file_search"
        assert self.detector.detect("where is the readme file") == "file_search"

    def test_web_search_intent(self):
        """Test detection of web search intent."""
        assert self.detector.detect("search for Python tutorials") == "web_search"
        assert self.detector.detect("look up weather forecast") == "web_search"
        assert self.detector.detect("what is machine learning") == "web_search"
        assert self.detector.detect("who is Albert Einstein") == "web_search"
        assert self.detector.detect("tell me about quantum physics") == "web_search"

    def test_default_intent(self):
        """Test default intent for unrecognized patterns."""
        assert self.detector.detect("hello there") == "default"
        assert self.detector.detect("how are you") == "default"
        assert self.detector.detect("random text") == "default"

    def test_edge_cases(self):
        """Test edge cases and empty inputs."""
        assert self.detector.detect("") == "default"
        assert self.detector.detect("   ") == "default"
        assert self.detector.detect("FIND THE FILE") == "file_search"  # Test case insensitivity

if __name__ == "__main__":
    pytest.main(["-v"])
