"""Application entry point for running the TECH5 Decision Support System."""

import sys

from app import create_app


def main() -> None:
    """Initializes and runs the integrated web application server."""
    app = create_app()
    port = 5000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    print(f" * Running TECH5 Application on http://127.0.0.1:{port}")
    print(" * Component A: Visualization & Recommendation mounted at /")
    print(" * Component B: Assignment Engine wired via Python contract")
    app.run(host="127.0.0.1", port=port, debug=True)


if __name__ == "__main__":
    main()
