from dependency_utils import install_missing


def main() -> int:
    for line in install_missing(auto_install=True):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
