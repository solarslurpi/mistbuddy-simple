import pytest

@pytest.fixture
def first():
    print("Set up first fixture")
    yield
    print("Clean up first fixture")


@pytest.fixture
def second(first):
    print("Set up second fixture")
    yield
    print("Clean up second fixture")


def test_context_fixture_order(second):
    print("In the test")
    assert False

if __name__ == "__main__":
    test_context_fixture_order(second)