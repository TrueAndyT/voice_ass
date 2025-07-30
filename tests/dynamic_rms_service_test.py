import pytest
import numpy as np
from services.dynamic_rms_service import DynamicRMSService

class TestDynamicRMSService:
    def setup_method(self):
        """Setup DynamicRMSService for testing."""
        self.rms_service = DynamicRMSService()
        self.rms_service.start()

    def test_update_threshold_with_silence(self):
        """Test RMS threshold update with silence audio."""
        silent_audio = np.zeros(480, dtype=np.int16).tobytes()
        self.rms_service.update_threshold(silent_audio)
        assert self.rms_service.get_threshold() == 0.0

    def test_update_threshold_with_noise(self):
        """Test RMS threshold update with noisy audio."""
        noisy_audio = (np.random.rand(480) * 32767).astype(np.int16).tobytes()
        self.rms_service.update_threshold(noisy_audio)
        assert self.rms_service.get_threshold() > 0.0

if __name__ == "__main__":
    pytest.main(["-v"])

