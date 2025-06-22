from ....data_classes import Fighter, FighterFrameData, ActionFrameData
from ....globals import Action

class Samurai(Fighter):
    """Powerful samurai with strong attacks but slow movement"""
    
    description = "Powerful samurai with strong attacks but slow movement"
    difficulty = 3
    style = "punisher"
    
    def __init__(self):
        frame_data = FighterFrameData({
            Action.ATTACK: ActionFrameData(
                action=Action.ATTACK,
                startup_frames=5,  # Slow startup
                active_frames=3,   # Longer active frames
                recovery_frames=8, # Long recovery
                damage=20,         # High damage
                knockback=10,
                stun_frames=15
            ),
            Action.JUMP: ActionFrameData(
                action=Action.JUMP,
                startup_frames=3,
                active_frames=14,
                recovery_frames=5
            ),
            Action.BLOCK: ActionFrameData(
                action=Action.BLOCK,
                startup_frames=2,
                active_frames=15,
                recovery_frames=3
            ),
        })
        
        super().__init__(
            name="Samurai",
            gravity=10.0,
            jump_force=12,
            move_speed=5,  # Slow movement
            x_attack_range=70,  # Long range (katana)
            y_attack_range=30,
            attack_damage=20,
            attack_cooldown=40,  # Long cooldown
            health=120,  # High health
            weapon="katana",
            frame_data=frame_data
        )