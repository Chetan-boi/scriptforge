from .utils import *
import sys

def main() -> None:
    # if no args run a menu driven approach
    if len(sys.argv) == 1:    # Only ran the file
        run_menu()
        return

    if len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h"):
        print_help()
        sys.exit()

    # if args invalid show usage
    if len(sys.argv) not in [4,3]:
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
