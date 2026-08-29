import pytest

from tests.infrastructure.textual.test_utils import eventually


class FakePilot:
    def __init__(self):
        self.pauses = 0

    async def pause(self) -> None:
        self.pauses += 1


@pytest.mark.asyncio
async def test_does_not_pause_when_the_condition_already_holds():
    pilot = FakePilot()

    await eventually(pilot, lambda: True, "an already satisfied condition")

    assert pilot.pauses == 0


@pytest.mark.asyncio
async def test_pauses_until_the_condition_holds():
    pilot = FakePilot()

    await eventually(pilot, lambda: pilot.pauses == 3, "three pauses")

    assert pilot.pauses == 3


@pytest.mark.asyncio
async def test_reports_the_description_when_the_condition_never_holds():
    pilot = FakePilot()

    with pytest.raises(AssertionError, match="a condition that never holds"):
        await eventually(
            pilot, lambda: False, "a condition that never holds", timeout=0.05
        )


@pytest.mark.asyncio
async def test_surfaces_the_error_a_failing_probe_raised():
    pilot = FakePilot()

    def probe() -> bool:
        raise LookupError("widget is not mounted")

    with pytest.raises(AssertionError) as failure:
        await eventually(pilot, probe, "a probe that keeps raising", timeout=0.05)

    assert isinstance(failure.value.__cause__, LookupError)
