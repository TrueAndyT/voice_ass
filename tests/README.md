# Voice Assistant Tests

This directory contains all test files for the Voice Assistant project. The tests are organized to validate different aspects of the system.

## Test Files

### `test_logging.py`
Tests the enhanced logging system including:
- Basic logging functionality with colors
- Performance metrics logging
- Exception handling and structured logging
- JSON log file generation

### `test_services.py`
Tests the service framework including:
- Service initialization
- Error handling framework
- Custom exception usage
- Service loader functionality

### `test_microservices.py`
Tests the microservices architecture including:
- Microservice startup and health checks
- HTTP communication between services
- Service isolation and fault tolerance
- Comprehensive integration testing

### `run_all_tests.py`
Comprehensive test runner that:
- Runs all available tests
- Provides detailed output and summaries
- Logs results for analysis
- Returns appropriate exit codes

## Running Tests

### Run Individual Tests
```bash
# Test the logging system
python3 tests/test_logging.py

# Test service framework
python3 tests/test_services.py

# Test microservices (requires services to be running)
python3 tests/test_microservices.py
```

### Run All Tests
```bash
# Run all tests with summary
python3 tests/run_all_tests.py
```

### Test Microservices
For microservices tests, you need to start the services first:
```bash
# Terminal 1: Start microservices
./start_services.sh

# Terminal 2: Run microservices tests
python3 tests/test_microservices.py

# Stop services when done
./stop_services.sh
```

## Test Output

Tests generate various log files in the `logs/` directory:
- `app.jsonl` - Structured JSON logs from all services
- `performance.jsonl` - Performance metrics and timing data
- `transcriptions.log` - STT transcription logs (if applicable)

## Adding New Tests

When adding new tests:
1. Create test files in this directory
2. Follow the naming convention `test_*.py`
3. Include proper imports with path adjustments
4. Add comprehensive docstrings
5. Update `run_all_tests.py` to include the new test
6. Update this README

## Test Coverage

The current test suite covers:
- ✅ Logging and error handling framework
- ✅ Service initialization and management
- ✅ Microservices architecture
- ✅ HTTP communication and health checks
- ✅ Performance monitoring and metrics

Future test additions should cover:
- [ ] Audio processing and STT functionality
- [ ] LLM response generation and quality
- [ ] TTS audio output validation
- [ ] Wake word detection accuracy
- [ ] End-to-end conversation flows
