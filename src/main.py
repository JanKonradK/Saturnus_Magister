import asyncio
import signal
import sys
from src.services.email_processor import EmailProcessor
from src.config import settings

async def main():
    # Check Python version
    if sys.version_info < (3, 14):
        print(f"Warning: Running Python {sys.version_info.major}.{sys.version_info.minor}")
        print("Recommended: Python 3.14 with free-threading (python3.14t)")

    # Check free-threading
    if hasattr(sys, '_is_gil_enabled'):
        if not sys._is_gil_enabled():
            print("✓ Free-threading enabled - parallel processing active")
        else:
            print("⚠ GIL enabled - consider using python3.14t for better performance")

    processor = EmailProcessor()
    await processor.initialize()

    # Graceful shutdown
    stop_event = asyncio.Event()

    def signal_handler():
        print("\nShutdown requested...")
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    print(f"Email processor started (polling every {settings.poll_interval_seconds}s)")
    print(f"Environment: {settings.environment.value}")
    print("Press Ctrl+C to stop.\n")

    try:
        while not stop_event.is_set():
            try:
                await processor.process_new_emails()
            except Exception as e:
                print(f"Error: {e}")

            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=settings.poll_interval_seconds
                )
            except asyncio.TimeoutError:
                pass
    finally:
        await processor.shutdown()
        print("Shutdown complete.")

def run():
    asyncio.run(main())

if __name__ == "__main__":
    run()
