"""Common base class for all integration adapters.

Every adapter reports honestly whether it is talking to a real service
("live") or to a local stand-in ("mock"). Mock adapters never pretend
that data was sent to an external system.
"""


class IntegrationAdapter:
    name = "integration"

    @property
    def is_live(self) -> bool:
        return False

    @property
    def mode(self) -> str:
        return "live" if self.is_live else "mock"

    def status(self) -> dict:
        raise NotImplementedError
