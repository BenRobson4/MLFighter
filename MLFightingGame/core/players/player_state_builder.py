import logging
from typing import Dict, List

from ..data_classes import PlayerState, ActionFrameData
from ..globals import Action, State
from .fighter_loader import FighterLoader

logger = logging.getLogger(__name__)

class PlayerStateBuilder:
    """Builder for creating PlayerState objects with proper initialization"""
    
    @staticmethod
    def build(player, player_id: int, spawn_x: float = 0.0, spawn_y: float = 0.0) -> PlayerState:
        """
        Generate a PlayerState object for this player at the start of combat
        
        Args:
            player_id: The player ID (1 or 2) for this combat instance
            spawn_x: Initial X position
            spawn_y: Initial Y position
            
        Returns:
            PlayerState object with all stats initialized from fighter and items
        """
        # Load fighter data based on player's fighter type
        fighter = player.fighter
        
        # Build frame data dictionary from fighter's frame data
        frame_data = {}
        for action in Action:
            action_data = fighter.get_action_data(action)
            frame_data[action] = [
                action_data.startup_frames,
                action_data.active_frames,
                action_data.recovery_frames
            ]
        
        # Determine facing direction based on player_id
        facing_right = (player_id == 1)
        
        # Create the PlayerState
        player_state = PlayerState(
            # Identity
            player_id=player_id,
            fighter_name=fighter.name.lower(),
            
            # Position and physics
            x=spawn_x,
            start_x=spawn_x,
            y=spawn_y,
            start_y=spawn_y,
            velocity_x=0.0,
            velocity_y=0.0,
            facing_right=facing_right,
            gravity=fighter.gravity,
            friction=fighter.friction,
            width=fighter.width,
            height=fighter.height,
            
            # Combat stats from fighter
            health=float(fighter.health),
            max_health=float(fighter.health),
            damage_reduction=float(fighter.damage_reduction),
            move_speed=float(fighter.move_speed),
            jump_force=float(fighter.jump_force),
            attack_damage=float(fighter.attack_damage),
            x_attack_range=float(fighter.x_attack_range),
            y_attack_range=float(fighter.y_attack_range),
            on_hit_stun=int(fighter.on_hit_stun),
            on_block_stun=int(fighter.on_block_stun),
            block_efficiency=float(fighter.block_efficiency),
            
            # Set state
            current_state=State.IDLE,
            state_frame_counter=0,
            
            # Status flags
            jump_cooldown=fighter.jump_cooldown,
            jump_cooldown_remaining=0,
            
            attack_cooldown=fighter.attack_cooldown,
            attack_cooldown_remaining=0,
            
            block_cooldown=fighter.block_cooldown,
            block_cooldown_remaining=0,
            
            got_stunned=False,
            stun_frames_remaining=0,
            
            # Action timing data
            frame_data=frame_data,
            
            # ML tracking (initialized empty)
            last_action_state=None,
            last_action_choice=None,
            requested_action=None,
            accumulated_reward=0.0,
            total_reward=0.0,
        )
        
        # Log the state generation
        logger.debug(f"Generated PlayerState for {player.player_id} (ID: {player_id}) at ({spawn_x}, {spawn_y})")
        logger.debug(f"Fighter stats: HP={fighter.health}, DMG={fighter.attack_damage}, SPD={fighter.move_speed}")
        
        return player_state