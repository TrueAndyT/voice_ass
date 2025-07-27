try:
    from services.logger import setup_logging
    print("✅ Successfully imported 'setup_logging'!")
except ImportError as e:
    print(f"❌ Failed to import 'setup_logging'.")
    print(f"Error: {e}")