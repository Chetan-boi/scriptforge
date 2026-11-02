from .extractor import *
from .generator import *

from rich.console import Console

import sys

console = Console()


def print_usage():
    console.print("""[bold cyan]Usage:[/bold cyan]
  [bold]GUI mode (default):[/bold]
    [green]uv run scriptforge[/green]
    [green]uv run scriptforge-gui[/green]

  [bold]Interactive CLI mode:[/bold]
    [green]uv run scriptforge-cli[/green]
    [green]uv run scriptforge --cli[/green]

  [bold]Direct CLI mode:[/bold]
    [green]uv run scriptforge-cli[/green] [yellow]<sample_image>[/yellow] [yellow]<text_data>[/yellow] [dim][output][/dim]

  [bold red]Options:[/bold red]
    [red]-h, --help[/red]    Show this help message and exit
    [yellow]--cli[/yellow]         Run in CLI mode when using `scriptforge`

[bold cyan]Arguments:[/bold cyan]
  [yellow]sample_image[/yellow]    Path to the scanned handwriting image/grid or existing .db profile
  [yellow]text_data[/yellow]       Text string or path to a .txt file to synthesize
  [dim]output[/dim]          (Optional) Output directory or target .pdf file path
                  [dim]Default: creates 'output.pdf' in the current directory[/dim]
""")


def display_menu():
    print("""
=== ScriptForge Menu ===
  1. Extract glyphs from image
  2. Synthesize text to PDF
  3. Exit
""")


def run_menu():
    while True:
        display_menu()
        choice = input("Select an option (1-3): ").strip()

        match choice:
            case "1":
                img_path = input("Enter handwriting image path: ")
                name = input("Enter the name: ")
                print(f"Extracting from: {img_path}")
                extract_glyphs(img_path, name)
            case "2":
                text = input("Enter .txt file path: ")
                out = input("Enter output PDF path or leave blank: ")
                name = input("Enter whose handwriting u want it to be in: ")
                print(f"Generating PDF: {out}")
                generate_pdf(text, out, name)

            case "3":
                print("Exiting ScriptForge.")
                sys.exit(0)

            case _:
                print("Invalid choice. Please enter a number from 1 to 3.")


def print_help():
    console.print("""
[bold cyan]ScriptForge[/bold cyan] - [dim]Handwritten PDF Synthesis & Desktop App[/dim]

[bold yellow]USAGE:[/bold yellow]
  [dim]# Graphical User Interface (Default)[/dim]
  [green]uv run scriptforge[/green]
  [green]uv run scriptforge-gui[/green]

  [dim]# Interactive CLI Menu[/dim]
  [green]uv run scriptforge-cli[/green]
  [green]uv run scriptforge --cli[/green]

  [dim]# Direct CLI Synthesis[/dim]
  [green]uv run scriptforge-cli[/green] [yellow]<sample_image>[/yellow] [yellow]<text_input>[/yellow] [dim][output_path][/dim]

[bold yellow]DESCRIPTION:[/bold yellow]
  ScriptForge converts typed text into realistic personalized handwriting.
  Launch the desktop GUI for an interactive notebook experience, or use the CLI
  to batch-extract glyphs and synthesize PDFs.

[bold yellow]MODES:[/bold yellow]
  [cyan]GUI Mode[/cyan]        Desktop app with live notebook text editor, settings, profile manager.
                  Run via: [green]uv run scriptforge[/green] or [green]uv run scriptforge-gui[/green]
  [cyan]CLI Mode[/cyan]        Terminal menu or one-shot script synthesis.
                  Run via: [green]uv run scriptforge-cli[/green] or [green]uv run scriptforge --cli[/green]

[bold yellow]ARGUMENTS (CLI):[/bold yellow]
  [cyan]<sample_image>[/cyan]    Path to the scanned handwriting sample or existing .db profile
  [cyan]<text_input>[/cyan]       Direct text string to synthesize or path to a [green].txt[/green] file
  [cyan][output_path][/cyan]      Target [green].pdf[/green] file or directory [dim](Default: ./output.pdf)[/dim]

[bold yellow]OPTIONS:[/bold yellow]
  [red]-h, --help[/red]        Display this help message and exit
  [yellow]--cli[/yellow]             Force CLI mode when launching via `scriptforge`

[bold yellow]EXAMPLES:[/bold yellow]
  [dim]# Launch the desktop GUI[/dim]
  [green]uv run scriptforge[/green]

  [dim]# Run interactive numbered CLI menu[/dim]
  [green]uv run scriptforge-cli[/green]

  [dim]# Synthesize using an inline string[/dim]
  [green]uv run scriptforge-cli[/green] sample.png [yellow]"Hello from ScriptForge"[/yellow] result.pdf

  [dim]# Synthesize using a text file and default output[/dim]
  [green]uv run scriptforge-cli[/green] assets/my_grid.jpg notes.txt
""")
