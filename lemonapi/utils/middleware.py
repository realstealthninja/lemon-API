from typing import Sequence
from aioprometheus import MetricsMiddleware, Registry
from aioprometheus.asgi.middleware import (
    ASGICallable,
)
from aioprometheus.mypy_types import LabelsType


# example labels: {"method": method, "path": path, "app_name": self.app_name}
class CustomMetricsMiddleware(MetricsMiddleware):
    def __init__(
        self,
        app: ASGICallable,
        registry: Registry = ...,
        exclude_paths: Sequence[str] = ...,
        use_template_urls: bool = True,
        group_status_codes: bool = False,
        const_labels: LabelsType | None = None,
    ) -> None:
        super().__init__(
            app,
            registry,
            exclude_paths,
            use_template_urls,
            group_status_codes,
            const_labels,
        )
