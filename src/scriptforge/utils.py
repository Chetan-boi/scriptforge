from .extractor import *
from .generator import *

from rich.console import Console

import sys

console = Console()

def print_usage():
    console.print("""[bold cyan]Usage:[/bold cyan]
  [bold]Interactive mode:[/bold]
    [green]uv run scriptforge[/green]

  [bold]Direct CLI mode:[/bold]
    [green]uv run scriptforge[/green] [yellow]<sample_image>[/yellow] [yellow]<text_data>[/yellow] [dim][output][/dim]

  [bold red]Options:[/bold red]
    [red]-h, --help[/red]    Show this help message and exit

[bold cyan]Arguments:[/bold cyan]
  [yellow]sample_image[/yellow]    Path to the scanned handwriting image/grid
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
[bold cyan]ScriptForge[/bold cyan] - [dim]Handwritten PDF Synthesis CLI[/dim]

[bold yellow]USAGE:[/bold yellow]
  [green]uv run scriptforge[/green] [dim][OPTIONS][/dim]
  [green]uv run scriptforge[/green] [yellow]<sample_image>[/yellow] [yellow]<text_input>[/yellow] [dim][output_path][/dim]

[bold yellow]DESCRIPTION:[/bold yellow]
  Extracts handwritten glyphs from a reference image sheet and 
  renders synthetic, personalized handwritten PDF documents.

[bold yellow]ARGUMENTS:[/bold yellow]
  [cyan]<sample_image>[/cyan]    Path to the scanned handwriting sample or grid image
  [cyan]<text_input>[/cyan]       Direct text string to synthesize or path to a [green].txt[/green] file
  [cyan][output_path][/cyan]      Target [green].pdf[/green] file or directory [dim](Default: ./output.pdf)[/dim]

[bold yellow]OPTIONS:[/bold yellow]
  [red]-h, --help[/red]        Display this help message and exit

[bold yellow]EXAMPLES:[/bold yellow]
  [dim]# Run interactive numbered menu[/dim]
  [green]uv run scriptforge[/green]

  [dim]# Synthesize using an inline string[/dim]
  [green]uv run scriptforge[/green] sample.png [yellow]"Hello from ScriptForge"[/yellow] result.pdf

  [dim]# Synthesize using a text file and default output[/dim]
  [green]uv run scriptforge[/green] assets/my_grid.jpg notes.txt
""")
