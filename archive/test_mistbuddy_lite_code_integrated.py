import asyncio
import pytest

@pytest.mark.skip(reason="Emulates a simple run. But takes a while so skipping after initial testing")
@pytest.mark.asyncio
async def test_start_mistbuddy(mistbuddy_controller, mistbuddy_state):
    await mistbuddy_controller.start(mistbuddy_state)

    # Let it run for a bit
    await asyncio.sleep(360)

    # Assert that the misting has started
    assert mistbuddy_controller.timer_task is not None
    assert not mistbuddy_controller.timer_task.done()

    # Now stop the misting process
    await mistbuddy_controller.stop()

    # Assert that the misting has stopped
    assert mistbuddy_controller.timer_task.done()