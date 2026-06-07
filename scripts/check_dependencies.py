from dependency_utils import check_dependencies


def main() -> int:
    for status in check_dependencies():
        label = "OK" if status.available else "MISSING"
        required = "required" if status.required else "optional"
        print(f"{label}: {status.name} ({required}) - {status.detail}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
