from . import ConnectionManager
import asyncio

def main():
    """Main entry point to start the server."""
    manager = ConnectionManager()
    asyncio.run(manager.start_server())

if __name__ == "__main__":
    main()