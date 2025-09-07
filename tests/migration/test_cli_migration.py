from percell.application.cli_parser import build_parser
from percell.adapters.cli_user_interface_adapter import CLIUserInterfaceAdapter


def test_cli_parser_has_expected_flags():
    p = build_parser()
    args = p.parse_args(["--input", "/in", "--output", "/out", "--data-selection"]) 
    assert args.input == "/in"
    assert args.output == "/out"
    assert args.data_selection is True


def test_cli_ui_adapter_basic_methods(capsys):
    ui = CLIUserInterfaceAdapter()
    ui.info("hello")
    ui.error("oops")
    out = capsys.readouterr()
    assert "hello" in out.out
    assert "oops" in out.out


