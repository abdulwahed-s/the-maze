# 🎮 Maze Runner - Procedural Maze Game

**Play the game now: [https://web-production-4e66.up.railway.app/](https://web-production-4e66.up.railway.app/)**

A procedurally generated maze game where you navigate through unique mazes to reach the exit as quickly as possible. Every maze is different, ensuring a fresh challenge every time you play!

## 🎯 Play Now!

**[🎮 Click here to play Maze Runner](https://web-production-4e66.up.railway.app/)**

No installation required - just open the link and start playing in your browser!

## ✨ Game Features

- **🎲 Unique Mazes**: Every game generates a completely new maze using procedural algorithms
- **⚡ Real-time Gameplay**: Smooth movement with keyboard (WASD/Arrow keys) or touch controls
- **🏆 Leaderboard**: Compete for the fastest completion time
- **📱 Mobile Friendly**: Works perfectly on phones, tablets, and desktop
- **🎨 Beautiful UI**: Modern, responsive design with smooth animations
- **🚀 Instant Start**: No downloads, no waiting - jump right into the action

## 🎮 How to Play

1. **Enter your name** and click "Start Game"
2. **Navigate the maze** using:
   - **Desktop**: Arrow keys or WASD
   - **Mobile**: Touch the directional buttons (▲◀▼▶)
3. **Find the exit** (orange square) starting from the blue square
4. **Beat your best time** and compete on the leaderboard!

## 🏆 Challenge Yourself

- **Speed Run**: How fast can you complete the maze?
- **Daily Challenge**: Every maze is unique - no memorization possible
- **Leaderboard**: Compare your times with other players
- **Mobile vs Desktop**: Try both platforms for different experiences

## 🚀 For Developers

### Local Development

Want to run the game locally or contribute to the project?

```bash
# Clone and run locally
git clone https://github.com/yourusername/the-maze.git
cd the-maze
pip install -r requirements.txt
python maze_game_standalone.py
```

### Key Technical Features

- **FastAPI Backend**: Modern Python web framework
- **Procedural Generation**: Depth-first search maze algorithm
- **SQLite Database**: Persistent leaderboard storage
- **Responsive Design**: Works on all devices and screen sizes
- **Real-time Updates**: Live timer and smooth animations

### Project Structure

```
the-maze/
├── maze_game_standalone.py    # Main game server and logic
├── requirements.txt           # Python dependencies
├── Procfile                  # Railway deployment config
└── README.md                 # This file
```

### Customization

Modify game settings in `maze_game_standalone.py`:

```python
GRID_SIZE = 20               # Maze dimensions (20x20)
CELL_PIXELS = 32             # Cell size in pixels
WALL_THICKNESS = 2           # Wall thickness
USE_ANIMATED_BUILD = False   # Animated maze generation
```

## 🌟 What Makes This Game Special?

- **No Two Mazes Alike**: Procedural generation ensures endless variety
- **Instant Gratification**: Click and play immediately
- **Cross-Platform**: Works on any device with a web browser
- **Competitive**: Leaderboard system encourages replayability
- **Open Source**: Built with modern web technologies

## 🤝 Contributing

We welcome contributions! Whether you're a developer or just have ideas:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

**Ready to play? [Click here to start your maze adventure!](https://web-production-4e66.up.railway.app/) 🎮✨**

*For questions or support, please open an issue on GitHub.*
