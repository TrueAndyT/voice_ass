"""
Custom exception classes for the voice assistant application.
Provides structured error handling with context and categorization.
"""

class VoiceAssistantException(Exception):
    """Base exception for all voice assistant errors."""
    
    def __init__(self, message: str, context: dict = None, recoverable: bool = True):
        super().__init__(message)
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = None
    
    def __str__(self):
        base_msg = super().__str__()
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{base_msg} (Context: {context_str})"
        return base_msg


class AudioException(VoiceAssistantException):
    """Exceptions related to audio processing."""
    pass


class MicrophoneException(AudioException):
    """Microphone access or configuration errors."""
    pass


class STTException(VoiceAssistantException):
    """Speech-to-text service errors."""
    pass


class LLMException(VoiceAssistantException):
    """Large Language Model service errors."""
    pass


class TTSException(VoiceAssistantException):
    """Text-to-speech service errors."""
    pass


class WakeWordException(VoiceAssistantException):
    """Wake word detection errors."""
    pass


class ServiceInitializationException(VoiceAssistantException):
    """Service loading and initialization errors."""
    
    def __init__(self, service_name: str, message: str, context: dict = None):
        super().__init__(message, context, recoverable=False)
        self.service_name = service_name


class ConfigurationException(VoiceAssistantException):
    """Configuration and setup errors."""
    
    def __init__(self, message: str, config_key: str = None, context: dict = None):
        super().__init__(message, context, recoverable=False)
        self.config_key = config_key


class ResourceException(VoiceAssistantException):
    """Resource management errors (files, network, etc.)."""
    pass


class ValidationException(VoiceAssistantException):
    """Data validation errors."""
    pass
