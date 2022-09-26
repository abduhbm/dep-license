import warnings

from dep_license import run


def main():
    return run()


if __name__ == "__main__":
    warnings.simplefilter("ignore", UserWarning)
    exit(main())
