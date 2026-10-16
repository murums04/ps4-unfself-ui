import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .converter import ConversionError, convert_file


def main():
    parser = argparse.ArgumentParser(description="Convert fake-signed PS4 SELF to ELF.")
    parser.add_argument("files", nargs="*", type=Path)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--convert", action="store_true", help="Convert without the UI")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--report", type=Path, help="New JSON report path (--convert)")
    parser.add_argument("--check-ui", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.convert:
        if not args.files or args.output_dir is None:
            parser.error("--convert requires input files and --output-dir")
        results = []
        for source in args.files:
            try:
                output = convert_file(source, args.output_dir)
                results.append({"source": str(source), "status": "converted", "output": str(output)})
            except ConversionError as error:
                results.append({"source": str(source), "status": "failed", "error": str(error)})
        if args.report:
            with args.report.open("x", encoding="utf-8") as report:
                json.dump(results, report, indent=2)
        elif sys.stdout is not None:
            print(json.dumps(results, indent=2))
        return int(any(result["status"] == "failed" for result in results))

    from PySide6.QtWidgets import QApplication
    from .window import MainWindow
    application = QApplication(sys.argv[:1])
    application.setApplicationName("PS4 Unfself UI")
    application.setOrganizationName("murums")
    application.setStyle("Fusion")
    window = MainWindow()
    window.add_files(args.files)
    window.show()
    if args.check_ui:
        from PySide6.QtCore import QTimer

        def record_ui():
            try:
                with args.check_ui.open("x", encoding="utf-8") as report:
                    json.dump({"visible": window.isVisible(), "width": window.width(),
                               "height": window.height(), "platform": application.platformName()}, report)
                application.exit(0)
            except OSError:
                application.exit(1)

        QTimer.singleShot(250, record_ui)
    else:
        window.update_checker.start_automatic_check()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())

