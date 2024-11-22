import os
import asyncio
import signal
from typing import List, Tuple, Optional
from enum import Enum, auto

class GameState(Enum):
    MENU = auto()
    LOADING = auto()
    IN_GAME = auto()
    SETTINGS = auto()
    CHARACTER_CREATION = auto()
    EXIT = auto()

class AsyncLobbyGUI:
    def __init__(self):
        self.title = """
        ╔══════════════════════════════════════════╗
        ║             EPIC RPG ADVENTURE           ║
        ╚══════════════════════════════════════════╝"""
        
        self.menu_options = [
            "1. Start New Game",
            "2. Load Game",
            "3. Character Creation",
            "4. Settings",
            "5. Credits",
            "6. Exit"
        ]
        self.selected_option = 0
        self.state = GameState.MENU
        self.running = True
        self.loading_task: Optional[asyncio.Task] = None
        self.background_tasks: List[asyncio.Task] = []
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        
    def draw_character_preview(self) -> str:
        return """
           /\\
          /  \\
         /    \\
        /      \\
       |   ○  ○ |
       |    ◡   |
        \\  --  /
         \\    /
          \\  /
           \\/"""
           
    def draw_menu(self) -> None:
        self.clear_screen()
        print(self.title)
        print("\n" + self.draw_character_preview())
        print("\n╔══════════════ MENU ══════════════╗")
        
        for idx, option in enumerate(self.menu_options):
            if idx == self.selected_option:
                print(f"║ > {option:<28} ║")
            else:
                print(f"║   {option:<28} ║")
                
        print("╚════════════════════════════════════╝")
        print("\nUse ↑↓ arrows to navigate and Enter to select")

    async def loading_animation(self) -> None:
        animations = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        try:
            while self.state == GameState.LOADING:
                for frame in animations:
                    if self.state != GameState.LOADING:
                        break
                    print(f"\rLoading {frame}", end="", flush=True)
                    await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            print("\rLoaded!    ")

    async def background_state_update(self) -> None:
        """Simulates background game state updates"""
        try:
            while self.running:
                await asyncio.sleep(1)
                # Add background tasks here (e.g., autosave, network sync, etc.)
        except asyncio.CancelledError:
            pass

    async def handle_input(self) -> None:
        if os.name == 'nt':  # Windows
            while self.running:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    await self.process_key_input(key)
                await asyncio.sleep(0.01)
        else:  # Unix-like
            import sys, tty, termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                while self.running:
                    if select.select([sys.stdin], [], [], 0)[0]:
                        ch = sys.stdin.read(1)
                        if ch == '\x1b':
                            next1, next2 = sys.stdin.read(2)
                            if next1 == '[':
                                if next2 == 'A':  # Up arrow
                                    self.selected_option = (self.selected_option - 1) % len(self.menu_options)
                                elif next2 == 'B':  # Down arrow
                                    self.selected_option = (self.selected_option + 1) % len(self.menu_options)
                        elif ch == '\r':  # Enter key
                            await self.handle_selection(self.menu_options[self.selected_option].split(". ")[1])
                    await asyncio.sleep(0.01)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    async def process_key_input(self, key: bytes) -> None:
        if key == b'\xe0':  # Special key prefix
            key = msvcrt.getch()
            if key == b'H':  # Up arrow
                self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            elif key == b'P':  # Down arrow
                self.selected_option = (self.selected_option + 1) % len(self.menu_options)
        elif key == b'\r':  # Enter key
            await self.handle_selection(self.menu_options[self.selected_option].split(". ")[1])

    async def handle_selection(self, selection: str) -> None:
        self.state = GameState.LOADING
        self.loading_task = asyncio.create_task(self.loading_animation())
        
        # Simulate some loading time
        await asyncio.sleep(2)
        
        if self.loading_task:
            self.loading_task.cancel()
            try:
                await self.loading_task
            except asyncio.CancelledError:
                pass

        if selection == "Exit":
            self.running = False
            self.state = GameState.EXIT
            print("\nThanks for playing!")
            return

        elif selection == "Start New Game":
            self.state = GameState.IN_GAME
            print("\nStarting new game...")
            
        elif selection == "Character Creation":
            self.state = GameState.CHARACTER_CREATION
            print("\nEntering character creation...")
            
        elif selection == "Settings":
            self.state = GameState.SETTINGS
            print("\nOpening settings...")
            
        await asyncio.sleep(1)
        self.state = GameState.MENU

    async def update_display(self) -> None:
        """Updates the display based on current state"""
        while self.running:
            if self.state == GameState.MENU:
                self.draw_menu()
            await asyncio.sleep(0.1)

    def handle_signal(self, signum, frame):
        """Handle system signals for clean shutdown"""
        self.running = False
        for task in self.background_tasks:
            task.cancel()

    async def run(self) -> None:
        # Set up signal handlers for clean shutdown
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        # Create and store background tasks
        self.background_tasks = [
            asyncio.create_task(self.background_state_update()),
            asyncio.create_task(self.update_display()),
            asyncio.create_task(self.handle_input())
        ]

        try:
            # Wait for all tasks to complete
            await asyncio.gather(*self.background_tasks, return_exceptions=True)
        finally:
            # Cleanup
            for task in self.background_tasks:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

async def entry():
    if os.name == 'nt':
        import msvcrt
    else:
        import select
    
    # Create and run the lobby
    lobby = AsyncLobbyGUI()
    await lobby.run()