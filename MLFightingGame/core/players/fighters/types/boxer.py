from ....data_classes import Fighter, FighterFrameData, ActionFrameData
from ....globals import Action

class Boxer(Fighter):
    """Fast boxer with quick jabs but lower health"""
    
    description = "Fast boxer with quick jabs but lower health"
    difficulty = 2
    style = "rushdown"
    
    def __init__(self):
        # Create custom frame data
        frame_data = FighterFrameData({
            Action.ATTACK: ActionFrameData(
                action=Action.ATTACK,
                startup_frames=2,  # Very fast startup
                active_frames=1,
                recovery_frames=3,  # Quick recovery
                damage=8,  # Lower damage per hit
                knockback=2
            ),
            Action.JUMP: ActionFrameData(
                action=Action.JUMP,
                startup_frames=1,
                active_frames=12,
                recovery_frames=2
            ),
            Action.BLOCK: ActionFrameData(
                action=Action.BLOCK,
                startup_frames=1,
                active_frames=8,
                recovery_frames=2
            ),
            # Other actions use defaults
        })
        
        super().__init__(
            name="Boxer",
            gravity=9.5,
            jump_force=15,
            move_speed=8,  # Fast movement
            x_attack_range=40,
            y_attack_range=20,
            attack_damage=8,
            attack_cooldown=15,  # Short cooldown
            health=80,  # Lower health
            weapon="fists",
            frame_data=frame_data
        )