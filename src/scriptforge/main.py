from .utils import *
import sys

def main() -> None:
    # if no args run a menu driven approach
    if len(sys.argv) == 1:    # Only ran the file
        run_menu()

    if len(sys.argv) == 2 and sys.argv[1] in ("--help", "-h"):
        print_help()
        sys.exit(1)

    # if args invalid show usage
    if len(sys.argv) not in [4,3]:
        print_usage()
        sys.exit(1)

    # there may be the following cases 
    # the args are [sample_png] [data text] [output pdf]
    # the args are [sample_png] [data text] 
    # the args are [sample_sqlite] [data text] [output pdf]
    # the args are [sample_sqlite] [data text]
    # the args are [sample_png] [output_sqlite]
