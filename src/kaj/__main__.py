from typing import NoReturn

from kaj.cli import cli_main


def main() -> NoReturn:
    raise SystemExit(cli_main())


if __name__ == "__main__":
    main()
