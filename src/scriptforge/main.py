import sys
from pathlib import Path

# Handle direct script execution vs package module import
if __package__ is None or __package__ == "":
    src_dir = Path(__file__).resolve().parent.parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from scriptforge.utils import extract_glyphs, generate_pdf, print_help, print_usage, run_menu
else:
    from .utils import extract_glyphs, generate_pdf, print_help, print_usage, run_menu


def cli() -> None:
    """CLI entry point"""
    # if no args run a menu driven approach
    if len(sys.argv) == 1:
        run_menu()
        return

    if len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h"):
        print_help()
        sys.exit(0)

    # if args invalid show usage
    if len(sys.argv) not in [3, 4]:
        print_usage()
        sys.exit(1)

    sample = sys.argv[1]
    text = sys.argv[2]
    out = sys.argv[3] if len(sys.argv) == 4 else None

    if sample.endswith(".db"):
        name = sample.removesuffix(".db")
    else:
        extract_glyphs(sample)
        name = None

    generate_pdf(text, out, name)


def gui_direct() -> None:
    """Direct GUI launcher."""
    if __package__ is None or __package__ == "":
        from scriptforge.gui import main as gui_main
    else:
        from .gui import main as gui_main
    gui_main()


def main() -> None:
    """Default entry point."""
    # When packaged as a standalone PyInstaller app, skip CLI entirely
    if getattr(sys, "frozen", False):
        gui_direct()
        return

    # Check if invoked as CLI command or explicitly with --cli flag
    invoked_name = Path(sys.argv[0]).stem.lower()
    if "cli" in invoked_name or (len(sys.argv) > 1 and sys.argv[1] == "--cli"):
        if len(sys.argv) > 1 and sys.argv[1] == "--cli":
            sys.argv.pop(1)
        cli()
        return

    print("Running Default mode : GUI")
    gui_direct()


if __name__ == "__main__":
    main()
