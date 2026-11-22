import sys

from src.slug import make_slug

MAX_ERROR = "error: --max must be an integer from 1 to 200"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    max_length = 60
    if "--max" in args:
        index = args.index("--max")
        value = args[index + 1] if index + 1 < len(args) else ""
        args = args[:index] + args[index + 2 :]
        if not value.isdigit() or not 1 <= int(value) <= 200:
            print(MAX_ERROR, file=sys.stderr)
            return 2
        max_length = int(value)
    if len(args) != 1:
        print("usage: python main.py TITLE [--max N]", file=sys.stderr)
        return 2
    try:
        print(make_slug(args[0], max_length))
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0
