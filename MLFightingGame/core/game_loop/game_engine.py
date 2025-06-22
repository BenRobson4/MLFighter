from . import GameState
from .. players import Player

class GameEngine:


    def step(self, game_state: GameState, player_1: Player, player_2: Player) -> GameState:
        """
        Perform a single step in the game loop, updating the game state.
        
        Args:
            game_state: Current state of the game
        
        Returns:
            Updated game state after processing actions and rewards
        """
        self.state = game_state

        self.player_1 = player_1
        self.player_2 = player_2

        self.player_1.state = self.state.get_player(1)
        self.player_2.state = self.state.get_player(2)

        self._get_actions()

        self._apply_actions()

        self._update_physics()
        
        self._handle_combat()
        
        self._calculate_rewards()

        self._end_frame_checks()

        return game_state
    
    def _get_actions(self):
        """Checks if either player can make an action and queries the model if they can make an action"""
        for player in [self.player_1, self.player_2]:
            if player.state.action_frame_counter < player.state.action_total_frames:
                continue
            else:
                player.state.current_action = player.get_action(self.state.get_state_vector(player.state.player_id))
                player.state.last_action_state = self.state.get_state_vector(player.state.player_id)
                player.state.last_action_choice = player.state.current_action

        

    def _update_physics(self):
        """Update physics for all players"""
        for player in [self.player_1.state, self.player_2.state]:
            gravity = player.gravity
            
            # Apply gravity
            if player.is_jumping:
                player.velocity_y += gravity
            
            # Update positions
            player.x += player.velocity_x
            player.y += player.velocity_y
            
            # Boundary checking
            player.x = max(50, min(self.state.arena_width - 50, player.x))
            
            # Ground collision
            if player.y >= self.state.ground_level:
                player.y = self.state.ground_level
                player.velocity_y = 0
                player.is_jumping = False
    
    def _calculate_rewards(self):
        """Calculate and store rewards for players who made decisions this frame"""
        for player in [self.player_1, self.player_2]:
            # Only calculate rewards if player made a decision this frame
            if player.state.last_action_state is not None and player.state.last_action_choice is not None:
                # Rewards are already accumulated in the player state during combat and physics
                
                # Get final reward for this action
                total_reward = player.state.accumulated_reward
                
                # Get state vectors for ML update
                current_state = player.state.last_action_state
                next_state = self.state.get_state_vector(player.state.player_id)
                done = self.state.is_game_over()
                
                # Update the ML agent
                player.update(
                    current_state, 
                    player.state.last_action_choice, 
                    total_reward, 
                    next_state, 
                    done
                )
                
                # Reset for next decision
                player.state.last_action_state = None
                player.state.last_action_choice = None
                
        #  Reset accumulated rewards for next frame
        self.game_state.reset_accumulated_rewards()
