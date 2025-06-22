from ..shop import ShopManager
from ..server import ConnectionManager

class GameManager:

    def __init__(self):
        """
        Initialize the game manager with necessary components.
        This includes setting up the game state, player connections, and initial configurations.
        """
        self.game_state = None  # Placeholder for the game state object
        self.players = []  # List to hold player objects
        self.game_finished = False  # Flag to indicate if the game has finished
        self.shop_manager = ShopManager
        self.connection_manager = ConnectionManager

    def play_game(self):

        # Network system for online play
        self._connect_players()

        # Initilisation steps before main game cycle
        self._create_initial_shop()

        self._configure_players()

        while not game_finished:

            self._run_fights()

            self._send_replays()

            self._shop_phase()

            self._update_players()

        self._send_end_info()

    def _connect_players(self):
        """
        Connect players to the game server or matchmaking system.
        This could involve network setup, player authentication, etc.
        """
        pass

    def _create_initial_shop(self):

        for player in self.players:
            # Create an initial shop for each player
            shop = self.shop_manager.create_initial_shop(player)
            self.connection_manager.send_shop_update(player, shop)