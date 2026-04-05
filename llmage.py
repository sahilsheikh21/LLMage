#!/usr/bin/env python3
"""CLI: convert a text prompt into SVG/PNG via litellm (supports OpenAI, Anthropic, Gemini, local, etc)."""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
import litellm
from litellm import completion
from litellm.exceptions import RateLimitError, APIError, APIConnectionError

# Suppress litellm output if desired
litellm.suppress_debug_info = True

CONFIG_DIR = Path.home() / ".llmage"
GLOBAL_ENV_PATH = CONFIG_DIR / ".env"

SYSTEM_INSTRUCTION = (
    "You are an expert SVG artist. You only respond with raw valid SVG code and nothing else. "
    "No markdown, no backticks, no explanation. Just the SVG tag and its contents."
)

HD_SYSTEM_INSTRUCTION = (
    "You are a Master SVG Illustrator specializing in premium, high-end vector art. "
    "Your goal is to create visually stunning, complex, and professional SVG images. "
    "Follow these STRICT rules:\n"
    "1. Use multi-layered <linearGradient> and <radialGradient> for realistic lighting and 3D depth.\n"
    "2. Use <filter> with <feGaussianBlur> for soft shadows, neon glows, and atmospheric effects.\n"
    "3. Use <cc> (Clip Paths) and complex <path> data for intricate shapes.\n"
    "4. Ensure high contrast and a harmonious professional color palette.\n"
    "5. Use varied stroke-widths and opacities to create texture.\n"
    "6. Respond ONLY with the raw <svg> code. No commentary or markdown."
)

PIXEL_SYSTEM_INSTRUCTION = (
    "You are a Legendary Sprite Artist for retro games. "
    "Your goal is to create high-quality, recognizable pixel art in a 32x32 grid. "
    "Follow these STRICT rules:\n"
    "1. You MUST use a 32x32 coordinate system. Every pixel is a 1x1 <rect>.\n"
    "2. Add shape-rendering=\"crispEdges\" to the <svg> tag.\n"
    "3. Use a BOLD DARK OUTLINE around your character to make it recognizable.\n"
    "4. Center the character and ensure it fills most of the 32x32 space.\n"
    "5. Use high-contrast colors (e.g., if it's Ben 10, use vibrant Green, White, and Black).\n"
    "6. Use simple 'shading' by using a slightly darker version of the base color on one side.\n"
    "7. Respond ONLY with the raw <svg> code."
)

RETRY_USER_SUFFIX = (
    "\n\nIMPORTANT: Your previous answer was rejected because it was not valid raw SVG. "
    "Reply again with ONLY a single valid SVG document: start with the character '<' as in <svg "
    "and end with </svg>. No markdown fences, no backticks, no commentary before or after."
)


def build_user_message(user_prompt: str, size: int, hd: bool = False, pixel: bool = False, res: int = 32) -> str:
    # If pixel mode is on, we'll force a fixed coordinate system inside the SVG
    v_size = res if pixel else size
    msg = (
        f"Create a detailed, colorful SVG image of: {user_prompt}. \n"
        "Requirements:\n"
        f"- viewBox must be 0 0 {v_size} {v_size}\n"
    )
    if pixel:
        msg += (
            f"- Technical Style: Retro Pixel Art/Sprite ({res}x{res} grid)\n"
            "- Use shape-rendering='crispEdges' for sharp pixels\n"
            "- Each 'pixel' should be a <rect> with width='1' and height='1'\n"
            f"- Use integer coordinates from 0 to {res-1} (e.g., x='5', y='10')\n"
            "- Center the character/object and make it large and recognizable\n"
        )
    elif hd:
        msg += (
            "- Use advanced SVG features: gradients, filters, masks, and shadows\n"
            "- Focus on artistic excellence and professional aesthetics\n"
            "- Create a full-scene composition with background elements\n"
            "- Use at least 150-300 distinct SVG elements for high detail\n"
        )
    else:
        msg += (
            "- Use rich colors and make it visually appealing\n"
            "- Include fine details like gradients, strokes, fills\n"
        )
    
    msg += (
        "- Must be valid SVG that renders correctly in a browser\n"
        "- Only output the raw SVG, starting with <svg and ending with </svg>"
    )
    return msg


def _strip_markdown_fences(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^```(?:svg|xml)?\s*", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*```\s*$", "", t)
    return t.strip()


def extract_svg(text: str) -> str | None:
    if not text:
        return None
    t = _strip_markdown_fences(text)
    lower = t.lower()
    start = lower.find("<svg")
    if start == -1:
        return None
    end = lower.rfind("</svg>")
    if end == -1:
        return None
    svg = t[start : end + len("</svg>")].strip()
    if not svg.lower().startswith("<svg"):
        return None
    return svg


def filename_from_prompt(prompt: str, max_words: int = 6, max_len: int = 48) -> str:
    words = re.findall(r"[a-zA-Z0-9]+", prompt.lower())[:max_words]
    base = "_".join(words) if words else "output"
    if len(base) > max_len:
        base = base[:max_len].rstrip("_")
    return base or "output"


def call_llm(model: str, messages: list[dict], console: Console, quota_retries: int = 2) -> str | None:
    """Returns response text, or None if the API call failed after retries."""
    last_exc: BaseException | None = None
    for attempt in range(quota_retries + 1):
        try:
            with console.status(f"[bold cyan]Generating image with {model}...", spinner="dots"):
                response = completion(
                    model=model,
                    messages=messages,
                )
            return response.choices[0].message.content
        except RateLimitError as e:
            last_exc = e
            wait = 8.0
            if attempt < quota_retries:
                console.print(
                    f"[yellow]Rate limit / quota (429). Waiting {wait:.1f}s, then retrying "
                    f"({attempt + 1}/{quota_retries})…[/yellow]",
                )
                time.sleep(wait)
            continue
        except (APIError, APIConnectionError, litellm.exceptions.OpenAIError, Exception) as e:
            console.print(f"[red]LLM API error:[/red] {e}")
            return None

    console.print(f"[red]Request to {model} failed after retries (quota or rate limit).[/red]")
    if last_exc is not None:
        console.print(f"[dim]{last_exc}[/dim]")
    return None


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate SVG (and optional PNG) from a text prompt using any LLM via litellm.",
    )
    p.add_argument(
        "prompt",
        nargs="*",
        help="Image description",
    )
    p.add_argument(
        "--format",
        choices=("svg", "png", "both"),
        default="both",
        help='Output format: "svg", "png", or "both" (default: both)',
    )
    p.add_argument(
        "--output",
        default=None,
        help="Output base filename without extension (default: derived from prompt)",
    )
    p.add_argument(
        "--size",
        type=int,
        default=500,
        help="Image size in px for viewBox (default: 500)",
    )
    p.add_argument(
        "--model",
        default=os.environ.get("LLMAGE_MODEL", "gemini/gemini-2.0-flash"),
        help="Model id, format: provider/model (default: gemini/gemini-2.0-flash, or LLMAGE_MODEL env var)",
    )
    p.add_argument(
        "--key",
        default=None,
        help="Temporary API key for this request",
    )
    p.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Resolution multiplier for PNG export (e.g. 2 for 2x size)",
    )
    p.add_argument(
        "--max-tokens",
        type=int,
        default=4000,
        help="Max tokens to generate (default: 4000)",
    )
    p.add_argument(
        "--temp",
        type=float,
        default=0.7,
        help="Temperature for generation (default: 0.7)",
    )
    p.add_argument(
        "--hd",
        action="store_true",
        help="Use high-detail instructions for better aesthetics",
    )
    p.add_argument(
        "--pixel",
        action="store_true",
        help="Use pixel art (Minecraft) style instructions",
    )
    p.add_argument(
        "--res",
        type=int,
        default=32,
        help="Pixel resolution (default: 32). High values like 64+ may hit token limits.",
    )
    return p.parse_args()


def show_help(console: Console):
    from rich.panel import Panel
    from rich.table import Table
    
    console.print(Panel("[bold cyan]LLMAGE: THE MANUAL[/bold cyan]", expand=False))
    
    table = Table(title="Quick Reference", show_header=True, header_style="bold magenta")
    table.add_column("Flag / Command", style="dim")
    table.add_column("What it does", style="green")
    table.add_column("Example", style="yellow")
    
    table.add_row("config", "Setup API keys (Gemini, Groq, etc.)", "llmage config")
    table.add_row("--pixel", "Minecraft / 8-Bit Mode", "--pixel")
    table.add_row("--res", "Pixel Resolution (16, 32, 64)", "--res 64")
    table.add_row("--hd", "High Detail (HD) Art", "--hd")
    table.add_row("--scale", "HD Scaling (2x, 4x, etc.)", "--scale 4")
    table.add_row("--model", "AI provider/model", "--model groq/...")
    table.add_row("--key", "Temporary API key", "--key gsk_...")
    
    console.print(table)
    
    console.print("\n[bold]PRO TIP: Prompts matter![/bold]")
    console.print("* [cyan]Pixel Mode:[/cyan] Use keywords like 'sprite', '8-bit', 'character mesh'.")
    console.print("* [cyan]HD Mode:[/cyan] Describe lighting, gradients, and shadows.")
    console.print("(Read the [underline]README.md[/underline] for full examples!)")

def setup_config(console: Console, args_list: list[str] = None):
    from rich.prompt import Prompt
    from dotenv import set_key
    
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not GLOBAL_ENV_PATH.exists():
        GLOBAL_ENV_PATH.touch()
    
    # Check if user provided arguments like 'llmage config gemini YOUR_KEY'
    if args_list and len(args_list) >= 2:
        provider = args_list[0].lower()
        api_key = args_list[1]
        key_name = f"{provider.upper()}_API_KEY"
        if provider == "openrouter":
            key_name = "OPENROUTER_API_KEY"
        
        set_key(str(GLOBAL_ENV_PATH), key_name, api_key)
        console.print(f"[bold green]✓ Saved {key_name} to {GLOBAL_ENV_PATH}[/bold green]")
        return

    console.print("[bold cyan]LLMAGE CONFIGURATION[/bold cyan]")
    provider = Prompt.ask("Choose Provider", choices=["gemini", "groq", "openrouter", "openai", "anthropic", "ollama", "deepseek", "mistral", "custom"], default="gemini")
    
    if provider == "ollama":
        base_url = Prompt.ask("Enter your Ollama Base URL", default="http://localhost:11434")
        set_key(str(GLOBAL_ENV_PATH), "OLLAMA_API_BASE", base_url)
        console.print(f"[bold green]✓ Saved OLLAMA_API_BASE to {GLOBAL_ENV_PATH}[/bold green]")
        return

    if provider == "custom":
        base_url = Prompt.ask("Enter Custom API Base URL (e.g., http://localhost:8080/v1)")
        api_key = Prompt.ask("Enter Custom API Key", password=True)
        set_key(str(GLOBAL_ENV_PATH), "CUSTOM_API_BASE", base_url)
        set_key(str(GLOBAL_ENV_PATH), "CUSTOM_API_KEY", api_key)
        console.print(f"[bold green]✓ Saved CUSTOM config to {GLOBAL_ENV_PATH}[/bold green]")
        return

    key_name = f"{provider.upper()}_API_KEY"
    if provider == "openrouter":
        key_name = "OPENROUTER_API_KEY"
    
    api_key = Prompt.ask(f"Enter your {key_name}", password=True)
    
    set_key(str(GLOBAL_ENV_PATH), key_name, api_key)
    console.print(f"[bold green]✓ Saved {key_name} to {GLOBAL_ENV_PATH}[/bold green]")

def main() -> int:
    console = Console()
    try:
        # 1. Load Local .env (current dir)
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
        # 2. Load Global .env (~/.llmage/.env)
        if GLOBAL_ENV_PATH.exists():
            load_dotenv(GLOBAL_ENV_PATH, override=False) # Don't override local if it exists
    except Exception:
        pass

    args = parse_args()

    # Check for custom commands
    if args.prompt:
        cmd = args.prompt[0].lower()
        if cmd == "help":
            show_help(console)
            return 0
        if cmd == "config":
            setup_config(console, args.prompt[1:])
            return 0

    if args.pixel and args.res > 64:
        console.print("[yellow]Warning: High resolution ( > 64) pixel art often exceeds LLM token limits and may result in incomplete images.[/yellow]")

    prompt = " ".join(args.prompt).strip()
    if not prompt:
        show_help(console)
        return 0

    size = max(1, args.size)
    base_name = args.output or filename_from_prompt(prompt)
    base_name = re.sub(r"[^\w\-]+", "_", base_name).strip("_") or "output"

    out_dir = Path.cwd() / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.pixel:
        sys_instr = PIXEL_SYSTEM_INSTRUCTION.replace("32x32", f"{args.res}x{args.res}")
    elif args.hd:
        sys_instr = HD_SYSTEM_INSTRUCTION
    else:
        sys_instr = SYSTEM_INSTRUCTION
    
    messages = [
        {"role": "system", "content": sys_instr},
        {"role": "user", "content": build_user_message(prompt, size, hd=args.hd, pixel=args.pixel, res=args.res)}
    ]

    def _call_llm_internal(msgs: list[dict], quota_retries: int = 2) -> str | None:
        last_exc: BaseException | None = None
        for attempt in range(quota_retries + 1):
            try:
                with console.status(f"[bold cyan]Generating image with {args.model}...", spinner="dots"):
                    # Determine if we need a custom api_base
                    api_base = None
                    current_key = args.key
                    
                    if args.model.startswith("ollama/"):
                        api_base = os.environ.get("OLLAMA_API_BASE")
                    elif args.model.startswith("custom/"):
                        api_base = os.environ.get("CUSTOM_API_BASE")
                        current_key = current_key or os.environ.get("CUSTOM_API_KEY")

                    response = completion(
                        model=args.model,
                        messages=msgs,
                        max_tokens=args.max_tokens,
                        temperature=args.temp,
                        api_key=current_key,
                        api_base=api_base,
                    )
                return response.choices[0].message.content
            except RateLimitError as e:
                last_exc = e
                wait = 8.0
                if attempt < quota_retries:
                    console.print(
                        f"[yellow]Rate limit / quota (429). Waiting {wait:.1f}s, then retrying "
                        f"({attempt + 1}/{quota_retries})…[/yellow]",
                    )
                    time.sleep(wait)
                continue
            except (APIError, APIConnectionError, litellm.exceptions.OpenAIError, Exception) as e:
                console.print(f"[red]LLM API error:[/red] {e}")
                return None

        console.print(f"[red]Request to {args.model} failed after retries (quota or rate limit).[/red]")
        if last_exc is not None:
            console.print(f"[dim]{last_exc}[/dim]")
        return None

    raw = _call_llm_internal(messages)
    if raw is None:
        return 1
    svg = extract_svg(raw)

    if svg is None:
        console.print("[yellow]No valid SVG in response; retrying once with a stricter instruction…[/yellow]")
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user", "content": RETRY_USER_SUFFIX})
        raw = _call_llm_internal(messages)
        if raw is None:
            return 1
        svg = extract_svg(raw)

    if svg is None:
        console.print(
            "[red]Model did not return valid SVG (expected content starting with <svg …> and ending with </svg>).[/red]",
        )
        return 1

    svg_path = out_dir / f"{base_name}.svg"
    png_path = out_dir / f"{base_name}.png"

    want_svg = args.format in ("svg", "both")
    want_png = args.format in ("png", "both")

    svg_saved = False
    if want_svg:
        svg_path.write_text(svg, encoding="utf-8")
        svg_saved = True

    png_ok = False
    if want_png:
        try:
            import resvg_py
            
            final_svg = svg
            if args.scale != 1.0:
                # Add width/height to SVG tag to force scaling in resvg
                # We extract the size from viewBox or just use the size arg
                actual_size = args.size * args.scale
                if args.pixel:
                    actual_size = args.res * args.scale
                
                # Check if width/height already exist, if not, add them
                if "width=" not in svg[:200]:
                    final_svg = svg.replace("<svg", f"<svg width=\"{actual_size}\" height=\"{actual_size}\"", 1)
                else:
                    final_svg = re.sub(r'width="[^"]+"', f'width="{actual_size}"', svg, count=1)
                    final_svg = re.sub(r'height="[^"]+"', f'height="{actual_size}"', final_svg, count=1)

            png_bytes = resvg_py.svg_to_bytes(svg_string=final_svg)
            png_path.write_bytes(png_bytes)
            png_ok = True
        except Exception as e:
            console.print(f"[yellow]PNG conversion failed ({e!s}); saving SVG as fallback.[/yellow]")
            if not svg_saved:
                svg_path.write_text(svg, encoding="utf-8")
                svg_saved = True

    console.print("[bold green]✓ Image generated![/bold green]")
    if svg_saved:
        console.print(f"[green]SVG saved:[/green] {svg_path}")
    if want_png and png_ok:
        console.print(f"[green]PNG saved:[/green] {png_path}")
    elif want_png and not png_ok:
        console.print("[yellow]PNG was not created (see warning above).[/yellow]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
