
import asyncio
from .connection_manager import ConnectionManager
from .coordinators.game_coordinator import GameCoordinator

async def main():
    # Create both components
    connection_manager = ConnectionManager(host="localhost", port=8765)
    game_coordinator = GameCoordinator()
    
    # Wire them together
    connection_manager.set_game_coordinator(game_coordinator)
    game_coordinator.set_connection_manager(connection_manager)
    
    # Start server
    print("Starting server on localhost:8765...")
    await connection_manager.start_server()

if __name__ == "__main__":
    asyncio.run(main())