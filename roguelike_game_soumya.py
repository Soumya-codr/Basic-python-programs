import random
import os

# --- Configuration ---
MAP_WIDTH = 40
MAP_HEIGHT = 20
ROOM_MAX_SIZE = 8
ROOM_MIN_SIZE = 4
MAX_ROOMS = 10
MAX_MONSTERS_PER_ROOM = 2

# --- Utility Functions ---

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

# --- Component Classes ---

class Fighter:
    """
    A component for any Entity that can fight.
    Holds combat-related properties.
    """
    def __init__(self, hp, defense, power):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power

    def take_damage(self, amount, messages):
        """Applies damage to this fighter."""
        damage = amount - self.defense
        if damage > 0:
            self.hp -= damage
            messages.append(f"{self.owner.name} takes {damage} damage!")
            if self.hp <= 0:
                messages.append(f"{self.owner.name} is dead!")
                self.owner.die()
        else:
            messages.append(f"{self.owner.name} blocks the attack!")

    def attack(self, target, messages):
        """Attacks a target Fighter."""
        damage = self.power
        messages.append(f"{self.owner.name} attacks {target.name}!")
        target.fighter.take_damage(damage, messages)

class BasicMonsterAI:
    """
    A simple AI component for monsters.
    The monster will move towards the player if adjacent,
    otherwise, it will move randomly.
    """
    def take_turn(self, game_map, player, messages):
        """The monster's turn logic."""
        monster = self.owner
        
        # Check if player is adjacent
        dx = player.x - monster.x
        dy = player.y - monster.y
        
        if abs(dx) <= 1 and abs(dy) <= 1:
            # Player is adjacent, attack!
            if player.fighter.hp > 0:
                monster.fighter.attack(player, messages)
        else:
            # Player is not adjacent, move randomly
            move_x = random.randint(-1, 1)
            move_y = random.randint(-1, 1)
            new_x = monster.x + move_x
            new_y = monster.y + move_y
            
            if not game_map.is_blocked(new_x, new_y):
                # Check if the new spot is occupied by another entity
                if not game_map.get_entity_at(new_x, new_y):
                    monster.move(move_x, move_y)

# --- Core Classes ---

class Entity:
    """
    A generic object in the game: player, monster, item, etc.
    It's a container for components (like Fighter or AI).
    """
    def __init__(self, x, y, char, name, blocks=False, fighter=None, ai=None):
        self.x = x
        self.y = y
        self.char = char
        self.name = name
        self.blocks = blocks  # Does this entity block movement?
        
        self.fighter = fighter
        if self.fighter:
            self.fighter.owner = self  # Link component to this entity

        self.ai = ai
        if self.ai:
            self.ai.owner = self  # Link component to this entity

    def move(self, dx, dy):
        """Updates the entity's position."""
        self.x += dx
        self.y += dy

    def die(self):
        """Handles the entity's death."""
        # For now, just change its appearance and block status
        self.char = '%'
        self.name = f"remains of {self.name}"
        self.blocks = False
        self.fighter = None
        self.ai = None

class Tile:
    """
    A tile on the map. It may or may not be blocked (wall)
    and may or may not block sight.
    """
    def __init__(self, char, blocked):
        self.char = char
        self.blocked = blocked

class Rect:
    """A utility class for representing a rectangular room."""
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        """Returns the center coordinates of the room."""
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def intersects(self, other):
        """Returns true if this rectangle intersects with another one."""
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

# --- Map Management ---

class GameMap:
    """
    Holds the game map, entities, and handles map creation.
    """
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()
        self.entities = []

    def initialize_tiles(self):
        """Fills the map with blocked 'wall' tiles."""
        return [[Tile('#', True) for y in range(self.height)] for x in range(self.width)]

    def create_room(self, rect):
        """Digs out a rectangular room in the map."""
        # +1 to prevent rooms from touching
        for x in range(rect.x1 + 1, rect.x2):
            for y in range(rect.y1 + 1, rect.y2):
                self.tiles[x][y].char = '.'
                self.tiles[x][y].blocked = False

    def create_h_tunnel(self, x1, x2, y):
        """Digs a horizontal tunnel."""
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].char = '.'
            self.tiles[x][y].blocked = False

    def create_v_tunnel(self, y1, y2, x):
        """Digs a vertical tunnel."""
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].char = '.'
            self.tiles[x][y].blocked = False
            
    def place_monsters(self, room):
        """Places monsters in a given room."""
        num_monsters = random.randint(0, MAX_MONSTERS_PER_ROOM)
        
        for i in range(num_monsters):
            # Choose a random location in the room
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            
            if not self.get_entity_at(x, y):
                # Create a monster
                fighter_component = Fighter(hp=10, defense=0, power=3)
                ai_component = BasicMonsterAI()
                monster = Entity(x, y, 'M', 'Monster', blocks=True, fighter=fighter_component, ai=ai_component)
                self.entities.append(monster)

    def make_map(self, player):
        """Generates the full map procedure."""
        rooms = []
        num_rooms = 0

        for r in range(MAX_ROOMS):
            w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
            x = random.randint(0, self.width - w - 1)
            y = random.randint(0, self.height - h - 1)

            new_room = Rect(x, y, w, h)
            
            # Check for intersections with other rooms
            failed = False
            for other_room in rooms:
                if new_room.intersects(other_room):
                    failed = True
                    break
            
            if not failed:
                self.create_room(new_room)
                (new_x, new_y) = new_room.center()

                if num_rooms == 0:
                    # This is the first room, place the player here
                    player.x = new_x
                    player.y = new_y
                else:
                    # Connect this room to the previous one
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()
                    
                    if random.randint(0, 1) == 1:
                        # Horizontal first, then vertical
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # Vertical first, then horizontal
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                # Add monsters to the new room
                self.place_monsters(new_room)
                rooms.append(new_room)
                num_rooms += 1

    def is_blocked(self, x, y):
        """Checks if a tile is blocked by a wall."""
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return self.tiles[x][y].blocked

    def get_entity_at(self, x, y):
        """Finds the blocking entity at a location."""
        for entity in self.entities:
            if entity.blocks and entity.x == x and entity.y == y:
                return entity
        return None

# --- Game Engine ---

def render_game(game_map, player, messages):
    """Draws the entire game state to the console."""
    clear_screen()
    
    # Draw the map
    for y in range(game_map.height):
        for x in range(game_map.width):
            # Check for entities at this location
            entity_char = None
            for entity in game_map.entities:
                if entity.x == x and entity.y == y:
                    entity_char = entity.char
                    break
            
            if entity_char:
                print(entity_char, end='')
            else:
                print(game_map.tiles[x][y].char, end='')
        print() # Newline after each row
        
    # Print Player Stats
    print("-" * MAP_WIDTH)
    print(f"Player HP: {player.fighter.hp}/{player.fighter.max_hp}  DEF: {player.fighter.defense}  ATK: {player.fighter.power}")
    
    # Print Messages
    print("-" * MAP_WIDTH)
    for msg in messages:
        print(msg)
    print("-" * MAP_WIDTH)


def handle_player_turn(player, game_map, messages):
    """Gets and handles player input."""
    action = input("> ")
    
    if not action:
        return 'did_nothing'
        
    key = action[0].lower()

    if key == 'q':
        return 'exit'

    if key == 'w':
        player_move_or_attack(player, 0, -1, game_map, messages)
    elif key == 's':
        player_move_or_attack(player, 0, 1, game_map, messages)
    elif key == 'a':
        player_move_or_attack(player, -1, 0, game_map, messages)
    elif key == 'd':
        player_move_or_attack(player, 1, 0, game_map, messages)
    else:
        return 'did_nothing'
        
    return 'turn_taken'

def player_move_or_attack(player, dx, dy, game_map, messages):
    """Handles player's move or attack action."""
    x = player.x + dx
    y = player.y + dy

    target = game_map.get_entity_at(x, y)

    if target:
        # It's an entity, attack it
        player.fighter.attack(target, messages)
    elif not game_map.is_blocked(x, y):
        # It's empty space, move
        player.move(dx, dy)
    else:
        # It's a wall
        messages.append("You bump into a wall.")


def main():
    """Main game function."""
    
    # --- Initialization ---
    clear_screen()
    print("Welcome to Python Roguelike!")
    print("Controls: W, A, S, D to move. Q to quit.")
    print("Starting game...")
    # input() # Removed this line which was causing the EOFError

    game_state = 'playing'
    messages = []

    # Create the player
    fighter_component = Fighter(hp=30, defense=2, power=5)
    player = Entity(0, 0, '@', 'Player', blocks=True, fighter=fighter_component)
    
    # Create the game map
    game_map = GameMap(MAP_WIDTH, MAP_HEIGHT)
    game_map.make_map(player)
    
    # Add player to the map's entity list
    game_map.entities.insert(0, player) # Player is always the first entity

    # --- Main Game Loop ---
    while game_state != 'exit':
        
        # Clear messages from the previous turn
        messages.clear()

        # Render the current state
        render_game(game_map, player, messages)
        
        if game_state == 'game_over':
            print("\n=== GAME OVER ===")
            print("Press Q to quit.")
            action = input("> ").lower()
            if action == 'q':
                game_state = 'exit'
            continue
            
        # Get and handle player action
        player_action = handle_player_turn(player, game_map, messages)
        
        if player_action == 'exit':
            game_state = 'exit'
            continue
            
        # If the player took a turn, let monsters take theirs
        if player_action == 'turn_taken' and game_state == 'playing':
            for entity in game_map.entities:
                if entity.ai:
                    entity.ai.take_turn(game_map, player, messages)
                    
                    # Check if the player died during the monster's turn
                    if player.fighter.hp <= 0:
                        game_state = 'game_over'
                        # Add one last render to show the death message
                        render_game(game_map, player, messages)
                        break

    print("Thanks for playing!")

if __name__ == "__main__":
    main()
