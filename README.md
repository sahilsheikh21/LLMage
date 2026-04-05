# 🎨 LLMage: Universal AI Vector Artist
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**LLMage** is a powerful CLI tool that uses Advanced AI to "code" vector graphics (SVG) and render them as high-quality PNGs. It supports any LLM provider (Gemini, Claude, Groq, Ollama, OpenAI) via the LiteLLM engine.

---

## 🚀 Quick Start (One-Liner Install)
Paste this into your terminal to install the tool globally:
```bash
pip install git+https://github.com/YOUR_USERNAME/Project-LLMage.git
```

---

## 📦 Requirements & Tech Stack
When you install LLMage, it automatically sets up these powerful tools:
*   **[LiteLLM](https://github.com/BerriAI/litellm)**: The core engine for connecting to 100+ AI models.
*   **[resvg-py](https://github.com/m-reid/resvg-py)**: A high-performance Rust-based SVG to PNG renderer.
*   **[Rich](https://github.com/Textualize/rich)**: For the premium terminal UI and progress tracking.
*   **[python-dotenv](https://github.com/theskumar/python-dotenv)**: Secure management of your API keys.

---

## 🛠️ Setup & Configuration
No more manual `.env` editing! Simply run the setup command:
```bash
llmage config
```
*Follow the interactive prompts to choose your provider (Gemini, Groq, local Ollama, etc.) and save your keys securely.*

---

## 🎨 Command Reference

| Flag | Description | Example |
| :--- | :--- | :--- |
| **`config`** | **Setup API Keys**. Interactively save your provider keys. | `llmage config` |
| **`--pixel`** | **8-Bit / Retro Mode**. Forces the AI to draw pixel-by-pixel. | `--pixel --res 32` |
| **`--hd`** | **High Definition**. Uses advanced lighting, gradients, and shadows. | `--hd` |
| **`--scale`** | **HD Resolution Scaling**. Multiplies the output PNG size. | `--scale 4` |
| **`--model`** | **AI Engine**. Switch between any LiteLLM provider. | `--model groq/llama3-70b` |
| **`--format`** | **Output Type**. Choose `svg`, `png`, or `both`. | `--format png` |

---

## 💎 Pro Prompting Guide

### 1. High-Detail Masterpieces (`--hd`)
Focus on **lighting** and **style**.
*   **Prompt:** `"A futuristic cybernetic heart made of glowing blue glass and chrome, dark background, cinematic lighting."`
*   **Command:** `llmage "..." --hd --scale 2`

### 2. Retro Game Sprites (`--pixel`)
Think in **grids** (16, 32, or 64).
*   **Prompt:** `"A tiny 8-bit wizard holding a glowing purple staff, retro game style."`
*   **Command:** `llmage "..." --pixel --res 32 --scale 10`

### 3. Local Generation (Ollama)
Run for free using your local hardware!
*   **Setup:** `llmage config` (select ollama)
*   **Command:** `llmage "A minimalist lion" --model ollama/llama3`

---

## ❓ Need a Cheat Sheet?
If you're in the terminal and get stuck, just type:
```bash
llmage help
```

---

## ⚙️ Technical Note: The 512px Limit
While you *can* set `--res 512`, please note:
*   **Token Usage**: High resolutions (anything above 64) require the AI to write thousands of lines of code. This can quickly hit the model's **Token Limit**, causing the image to be cut off.
*   **Speed**: Generating 512x512 actual pixels via code is very slow and may fail on most providers.

> [!TIP]
> **The Pro Way:** For the best high-res results, use a lower grid resolution (like `--res 32` or `64`) and combine it with the **`--scale`** flag.
> *   *Example:* `llmage "dragon" --pixel --res 64 --scale 8` (This gives you a massive, sharp image without hitting token limits!)

---

## 🤝 Contributing
Feel free to open issues or pull requests. Let's make AI-generated vector art accessible to everyone!
