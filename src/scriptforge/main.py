import sys
from pathlib import Path
from .utils import extract_glyphs, generate_pdf, print_help, print_usage, run_menu


def cli() -> None:
    """CLI entry point for ScriptForge."""
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
    """Direct GUI launcher without checking --cli flag."""
    from .gui import main as gui_main
    gui_main()


def main() -> None:
    """Default entry point: launches GUI, or CLI if invoked as scriptforge-cli / with --cli."""
    # When packaged as a standalone PyInstaller app, skip CLI entirely
    if getattr(sys, "frozen", False):
        from .gui import main as gui_main
        gui_main()
        return

    # Check if invoked as CLI command or explicitly with --cli flag
    invoked_name = Path(sys.argv[0]).stem.lower()
    if "cli" in invoked_name or (len(sys.argv) > 1 and sys.argv[1] == "--cli"):
        if len(sys.argv) > 1 and sys.argv[1] == "--cli":
            sys.argv.pop(1)
        cli()
        return

    print("Running Default mode : GUI")
    from .gui import main as gui_main
    gui_main()


if __name__ == "__main__":
    main()
