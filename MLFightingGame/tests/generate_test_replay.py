import json
from datetime import datetime
from enum import Enum

class Action(Enum):
    LEFT = 0
    RIGHT = 1
    JUMP = 2
    BLOCK = 3
    ATTACK = 4
    IDLE = 5

class State(Enum):
    NONE = 0
    STARTUP = 1
    ACTIVE = 2
    RECOVERY = 3
    WAIT = 4

def pack_states(attack_state, block_state, jump_state, is_stunned=False):
    """Pack state information into a single integer"""
    flags = 0
    flags |= (attack_state.value & 0x7)
    flags |= ((block_state.value & 0x7) << 3)
    flags |= ((jump_state.value & 0x7) << 6)
    if is_stunned:
        flags |= (1 << 9)
    return flags

def generate_test_replay():
    """Generate comprehensive test replay with state system"""
    
    # Initialize replay data structure
    replay_data = {
        'metadata': {
            'arena_width': 800,
            'ground_level': 500,
            'max_frames': 600,
            'player_configs': {
                '1': {
                    'fighter_type': 'warrior',
                    'max_health': 100,
                    'attack_damage': 10,
                    'width': 64,
                    'height': 128,
                    'gravity': 0.8,
                    'action_durations': {
                        'attack': 24,  # 8 startup + 4 active + 12 recovery
                        'block': 23,   # 3 startup + 15 active + 5 recovery
                        'jump': 33     # 5 startup + 20 air time + 8 recovery
                    }
                },
                '2': {
                    'fighter_type': 'ninja',
                    'max_health': 80,
                    'attack_damage': 15,
                    'width': 60,
                    'height': 120,
                    'gravity': 0.8,
                    'action_durations': {
                        'attack': 20,  # 6 startup + 3 active + 11 recovery
                        'block': 18,   # 2 startup + 12 active + 4 recovery
                        'jump': 30     # 4 startup + 19 air time + 7 recovery
                    }
                }
            }
        },
        'frames': []
    }
    
    ground_level = 500.0
    frames = []
    
    # Player positions and states
    p1_x, p1_y = 200.0, ground_level
    p2_x, p2_y = 600.0, ground_level
    p1_health, p2_health = 100.0, 80.0
    
    # State durations for each player
    p1_jump_frames = {'startup': 5, 'air_time': 20, 'recovery': 8}
    p1_attack_frames = {'startup': 8, 'active': 4, 'recovery': 12}
    p1_block_frames = {'startup': 3, 'active': 15, 'recovery': 5}
    
    p2_jump_frames = {'startup': 4, 'air_time': 19, 'recovery': 7}
    p2_attack_frames = {'startup': 6, 'active': 3, 'recovery': 11}
    p2_block_frames = {'startup': 2, 'active': 12, 'recovery': 4}
    
    frame_counter = 0
    
    # === SEQUENCE 1: Basic Movement (frames 0-59) ===
    print("Generating movement sequence...")
    for i in range(60):
        # P1 moves right
        p1_x += 2.0
        p1_action = Action.RIGHT
        p1_facing = True
        
        # P2 moves left
        p2_x -= 2.0
        p2_action = Action.LEFT
        p2_facing = False
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': p1_health,
                'a': p1_action.value,
                'fr': p1_facing,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': p2_health,
                'a': p2_action.value,
                'fr': p2_facing,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # === SEQUENCE 2: Jump Test (frames 60-92) ===
    print("Generating jump sequence...")
    jump_start_frame = frame_counter
    
    for i in range(33):  # Total jump duration for P1
        # P1 jumping
        if i < p1_jump_frames['startup']:
            p1_jump_state = State.STARTUP
            p1_action = Action.JUMP
            # Stay on ground during startup
        elif i < p1_jump_frames['startup'] + p1_jump_frames['air_time']:
            p1_jump_state = State.WAIT  # CHANGED: Using WAIT for air time
            p1_action = Action.JUMP
            # Arc motion during air time
            progress = (i - p1_jump_frames['startup']) / p1_jump_frames['air_time']
            # Parabolic arc
            height = 150 * (1 - (2 * progress - 1) ** 2)
            p1_y = ground_level - height
        else:
            p1_jump_state = State.RECOVERY
            p1_action = Action.JUMP
            # Back on ground during recovery
            p1_y = ground_level
        
        # P2 stays idle
        p2_action = Action.IDLE
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': p1_health,
                'a': p1_action.value,
                'fr': True,
                'flags': pack_states(State.NONE, State.NONE, p1_jump_state)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': p2_health,
                'a': p2_action.value,
                'fr': False,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # === SEQUENCE 3: Attack Test (frames 93-116) ===
    print("Generating attack sequence...")
    attack_start_frame = frame_counter
    
    for i in range(24):  # Total attack duration for P1
        # P1 attacking
        if i < p1_attack_frames['startup']:
            p1_attack_state = State.STARTUP
            p1_action = Action.ATTACK
        elif i < p1_attack_frames['startup'] + p1_attack_frames['active']:
            p1_attack_state = State.ACTIVE
            p1_action = Action.ATTACK
            # Deal damage on first active frame
            if i == p1_attack_frames['startup']:
                p2_health -= 10.0
        else:
            p1_attack_state = State.RECOVERY
            p1_action = Action.ATTACK
        
        # P2 gets hit and stunned during P1's active frames
        if p1_attack_state == State.ACTIVE:
            p2_is_stunned = True
            p2_action = Action.IDLE
        else:
            p2_is_stunned = False
            p2_action = Action.IDLE
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': p1_health,
                'a': p1_action.value,
                'fr': True,
                'flags': pack_states(p1_attack_state, State.NONE, State.NONE)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': round(p2_health, 1),
                'a': p2_action.value,
                'fr': False,
                'flags': pack_states(State.NONE, State.NONE, State.NONE, p2_is_stunned)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # === SEQUENCE 4: Block Test (frames 117-139) ===
    print("Generating block sequence...")
    block_start_frame = frame_counter
    
    for i in range(23):  # Total block duration for P1
        # P1 blocking
        if i < p1_block_frames['startup']:
            p1_block_state = State.STARTUP
            p1_action = Action.BLOCK
        elif i < p1_block_frames['startup'] + p1_block_frames['active']:
            p1_block_state = State.ACTIVE
            p1_action = Action.BLOCK
        else:
            p1_block_state = State.RECOVERY
            p1_action = Action.BLOCK
        
        # P2 idle
        p2_action = Action.IDLE
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': p1_health,
                'a': p1_action.value,
                'fr': True,
                'flags': pack_states(State.NONE, p1_block_state, State.NONE)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': p2_health,
                'a': p2_action.value,
                'fr': False,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # === SEQUENCE 5: P2 Actions (frames 140-200) ===
    print("Generating P2 action sequence...")
    
    # P2 Jump
    for i in range(30):  # P2 jump duration
        # P2 jumping
        if i < p2_jump_frames['startup']:
            p2_jump_state = State.STARTUP
            p2_action = Action.JUMP
        elif i == p2_jump_frames['startup']:
            p2_jump_state = State.ACTIVE
            p2_action = Action.JUMP
            # Stay on ground during startup
            p2_y = ground_level
        elif i < p2_jump_frames['startup'] + p2_jump_frames['air_time']:
            p2_jump_state = State.WAIT  # CHANGED: Using WAIT for air time
            p2_action = Action.JUMP
            progress = (i - p2_jump_frames['startup']) / p2_jump_frames['air_time']
            height = 130 * (1 - (2 * progress - 1) ** 2)
            p2_y = ground_level - height
        else:
            p2_jump_state = State.RECOVERY
            p2_action = Action.JUMP
            p2_y = ground_level
        
        # P1 idle
        p1_action = Action.IDLE
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': p1_health,
                'a': p1_action.value,
                'fr': True,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': p2_health,
                'a': p2_action.value,
                'fr': False,
                'flags': pack_states(State.NONE, State.NONE, p2_jump_state)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # P2 Attack
    for i in range(20):  # P2 attack duration
        # P2 attacking
        if i < p2_attack_frames['startup']:
            p2_attack_state = State.STARTUP
            p2_action = Action.ATTACK
        elif i < p2_attack_frames['startup'] + p2_attack_frames['active']:
            p2_attack_state = State.ACTIVE
            p2_action = Action.ATTACK
            if i == p2_attack_frames['startup']:
                p1_health -= 15.0
        else:
            p2_attack_state = State.RECOVERY
            p2_action = Action.ATTACK
        
        # P1 gets hit
        if p2_attack_state == State.ACTIVE:
            p1_is_stunned = True
            p1_action = Action.IDLE
        else:
            p1_is_stunned = False
            p1_action = Action.IDLE
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': round(p1_health, 1),
                'a': p1_action.value,
                'fr': True,
                'flags': pack_states(State.NONE, State.NONE, State.NONE, p1_is_stunned)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': p2_health,
                'a': p2_action.value,
                'fr': False,
                'flags': pack_states(p2_attack_state, State.NONE, State.NONE)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # === SEQUENCE 6: Complex Combat (frames 201-300) ===
    print("Generating complex combat sequence...")
    
    # Move closer together
    for i in range(20):
        p1_x += 3.0
        p2_x -= 3.0
        p1_action = Action.RIGHT
        p2_action = Action.LEFT
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': p1_health,
                'a': p1_action.value,
                'fr': True,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': p2_health,
                'a': p2_action.value,
                'fr': False,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # Simultaneous attacks with block
    for i in range(24):  # P1 attack duration
        # P1 attacking
        if i < p1_attack_frames['startup']:
            p1_attack_state = State.STARTUP
            p1_action = Action.ATTACK
        elif i < p1_attack_frames['startup'] + p1_attack_frames['active']:
            p1_attack_state = State.ACTIVE
            p1_action = Action.ATTACK
        else:
            p1_attack_state = State.RECOVERY
            p1_action = Action.ATTACK
        
        # P2 blocking (starts slightly before P1's active frames)
        if i >= 6 and i < 6 + 18:  # P2 block duration
            block_i = i - 6
            if block_i < p2_block_frames['startup']:
                p2_block_state = State.STARTUP
                p2_action = Action.BLOCK
            elif block_i < p2_block_frames['startup'] + p2_block_frames['active']:
                p2_block_state = State.ACTIVE
                p2_action = Action.BLOCK
                # Blocked damage (reduced)
                if p1_attack_state == State.ACTIVE and block_i == p2_block_frames['startup']:
                    p2_health -= 3.0  # Reduced damage due to block
            else:
                p2_block_state = State.RECOVERY
                p2_action = Action.BLOCK
        else:
            p2_block_state = State.NONE
            p2_action = Action.IDLE
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': p1_health,
                'a': p1_action.value,
                'fr': True,
                'flags': pack_states(p1_attack_state, State.NONE, State.NONE)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': round(p2_health, 1),
                'a': p2_action.value,
                'fr': False,
                'flags': pack_states(State.NONE, p2_block_state, State.NONE)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # === SEQUENCE 7: Final movements and idle ===
    print("Generating final sequence...")
    remaining_frames = 400 - frame_counter
    
    for i in range(remaining_frames):
        # Both players idle
        p1_action = Action.IDLE
        p2_action = Action.IDLE
        
        frame_data = {
            'f': frame_counter,
            'p1': {
                'x': round(p1_x, 1),
                'y': round(p1_y, 1),
                'h': p1_health,
                'a': p1_action.value,
                'fr': True,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            },
            'p2': {
                'x': round(p2_x, 1),
                'y': round(p2_y, 1),
                'h': p2_health,
                'a': p2_action.value,
                'fr': False,
                'flags': pack_states(State.NONE, State.NONE, State.NONE)
            }
        }
        frames.append(frame_data)
        frame_counter += 1
    
    # Add frames to replay data
    replay_data['frames'] = frames
    
    # Add final metadata
    replay_data['metadata']['total_frames'] = len(frames)
    replay_data['metadata']['winner'] = 2 if p2_health > p1_health else 1
    replay_data['metadata']['timestamp'] = datetime.now().isoformat()
    
    # Save as JSON (not compressed)
    filename = 'test_replay.json'
    with open(filename, 'w') as f:
        json.dump(replay_data, f, indent=2)
    
    print(f"\nTest replay generated successfully!")
    print(f"Filename: {filename}")
    print(f"Total frames: {len(frames)}")
    print(f"Final health - P1: {p1_health:.1f}, P2: {p2_health:.1f}")
    print(f"Winner: Player {replay_data['metadata']['winner']}")
    print(f"\nSequence breakdown:")
    print(f"  Frames 0-59: Movement test")
    print(f"  Frames 60-92: P1 Jump test (WAIT state during air time)")
    print(f"  Frames 93-116: P1 Attack test")
    print(f"  Frames 117-139: P1 Block test")
    print(f"  Frames 140-169: P2 Jump test (WAIT state during air time)")
    print(f"  Frames 170-189: P2 Attack test")
    print(f"  Frames 190-209: Movement")
    print(f"  Frames 210-233: P1 Attack vs P2 Block")
    print(f"  Frames 234-399: Idle")

if __name__ == "__main__":
    generate_test_replay()