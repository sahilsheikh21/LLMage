# 🎨 LLMage: Make Images With Text Only LLM
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**LLMage** is a an CLI tool to generate high-quality images (SVG/PNG) from any AI model even text-only LLMs. By treating SVG code as a bridge, it allows models like Llama 3, Claude, or GPT-4o-mini to "draw" intricate vector graphics and render them as professional PNGs.

---

## 🚀 One-Liner Installation
Install LLMage globally to start generating art from your terminal:
```bash
pip install git+https://github.com/sahilsheikh21/LLMage.git
```
Steps:

<img src="https://readme-typing-svg.demolab.com?font=Share+Tech+Mono&size=22&duration=3000&pause=1000&color=4AF626&center=true&vCenter=true&width=750&lines=pip+install+git%2Bhttps%3A%2F%2Fgithub.com%2Fsahilsheikh21%2FLLMage.git;llmage;llmage+%22Draw+an+Blue+Circle%22+--model+ollama%2Fllama3" alt="Typing SVG" />
---

## Key Features
*    **Text-to-Vector**: Turn pure text prompts into clean, scalable SVG graphics.
*    **Platform Agnostic**: Supports 100+ models via [LiteLLM](https://github.com/BerriAI/litellm) (Gemini, Groq, Ollama, OpenAI, Claude).
*    **High-Speed Rendering**: Powered by [resvg-py](https://github.com/m-reid/resvg-py) for instant, high-quality PNG outputs.
*    **Retro Mode**: Generate authentic 8-bit/pixel-art styles with `--pixel`.
*    **HD Scaling**: Scale images up to any resolution without losing sharpness.
*    **Interactive Config**: Switch providers and manage API keys effortlessly with `llmage config`.

---

## 🛠️ How It Works
1.  **The Prompt**: You provide a creative description.
2.  **The "Artist"**: LLMage instructs your chosen AI model to write optimized SVG code.
3.  **The "Printer"**: The SVG is instantly rendered into a high-quality PNG using the `resvg` engine.

---

## 🎨 Command Reference

| Command / Flag | Description | Example |
| :--- | :--- | :--- |
| **`config`** | **Interactive Setup**. Configure API keys and providers. | `llmage config` |
| **`"prompt"`** | **Generate Art**. The main prompt for the image. | `llmage "A minimalist fox"` |
| **`--pixel`** | **Retro 8-Bit**. Forces the AI into grid-based drawing. | `--pixel --res 32` |
| **`--hd`** | **High Detail**. Adds advanced lighting and shadows. | `--hd` |
| **`--scale`** | **Output Quality**. Multiplier for the final PNG size. | `--scale 4` |
| **`--model`** | **Model Selection**. Switch models on the fly. | `--model groq/llama3-70b` |
| **`--format`** | **File Output**. Save as `svg`, `png`, or `both`. | `--format png` |

---

## 💎 Pro Prompting Guide

### 1. High-Detail Masterpieces (`--hd`)
Perfect for logos, icons, and modern art.
*   **Prompt:** `"A futuristic holographic prism floating in void, neon refraction, 4k detail."`
*   **Command:** `llmage "..." --hd --scale 2`

### 2. Retro Game Sprites (`--pixel`)
Optimized for 16x16, 32x32, or 64x64 grids.
*   **Prompt:** `"A tiny pixel-art slime monster, neon green, dark outlines."`
*   **Command:** `llmage "..." --pixel --res 32 --scale 10`

### 3. Local & Free (Ollama)
No API keys? No problem. Use Ollama locally.
*   **Command:** `llmage "A minimalist geometric bear" --model ollama/llama3`

### 4. High Performance with Cloud Model
Lightning fast generation using Cloud (Openai,Anthropic,Gemini,..) Models.
*   **Prompt:** `"A vibrant green circle with a smaller white circle perfectly centered inside."`
*   **Command:** `llmage "..." --model groq/llama-3.3-70b-versatile --hd`
---

## ⚙️ The "Pro Tip" for High Resolution
Generating a 1024x1024 grid via raw code is slow and hits AI token limits. 
> [!TIP]
> **Use the Grid + Scale combo:** Generate a low-resolution grid (e.g., `--res 64`) and use **`--scale`** to make it massive.
> *Example:* `llmage "dragon" --pixel --res 64 --scale 16`
> *Result: A sharp, high-res image without hitting AI limits!*

---

## 🤝 Contributing & License
LLMage is open-source under the **MIT License**. Feel free to fork, contribute, or open issues to help us make AI art accessible to everyone.
