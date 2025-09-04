from percell.ports.outbound.macro_runner_port import MacroRunnerPort, MacroResult


class FakeMacroRunner(MacroRunnerPort):
    def run_macro(self, macro_name: str, parameters: dict) -> MacroResult:
        ok = macro_name == 'test.ijm' and isinstance(parameters, dict)
        return MacroResult(success=ok, stdout='ok' if ok else 'fail')

    def validate_macro(self, macro_name: str) -> bool:
        return macro_name.endswith('.ijm')


def test_macro_runner_contract():
    runner = FakeMacroRunner()
    assert runner.validate_macro('a.ijm') is True
    assert runner.validate_macro('nope.txt') is False
    result = runner.run_macro('test.ijm', {"x": 1})
    assert result.success is True
    assert result.stdout == 'ok'
