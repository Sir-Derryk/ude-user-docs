# engine/tests/test_interfaces.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
from ude.interfaces import (
    BaseParser,
    BaseRenderer,
    UdeException,
    ParserError,
    RendererError,
)
from ude.models import ProjectCatalog


def test_abstract_class_instantiation_prevention():
    """Verify that BaseParser and BaseRenderer cannot be instantiated directly."""
    with pytest.raises(TypeError) as excinfo:
        BaseParser()
    assert "Can't instantiate abstract class BaseParser" in str(excinfo.value)

    with pytest.raises(TypeError) as excinfo:
        BaseRenderer()
    assert "Can't instantiate abstract class BaseRenderer" in str(excinfo.value)


def test_incomplete_subclass_instantiation_prevention():
    """Verify that subclasses that fail to implement abstract methods cannot be instantiated."""

    class IncompleteParser(BaseParser):
        pass

    with pytest.raises(TypeError) as excinfo:
        IncompleteParser()
    assert "Can't instantiate abstract class IncompleteParser" in str(excinfo.value)

    class IncompleteRenderer(BaseRenderer):
        pass

    with pytest.raises(TypeError) as excinfo:
        IncompleteRenderer()
    assert "Can't instantiate abstract class IncompleteRenderer" in str(excinfo.value)


def test_concrete_subclass_instantiation():
    """Verify that a fully conforming concrete subclass can be instantiated successfully."""

    class ConcreteParser(BaseParser):
        def parse(self, input_path: str) -> ProjectCatalog:
            return ProjectCatalog()

    parser = ConcreteParser()
    assert isinstance(parser.parse("dummy"), ProjectCatalog)

    class ConcreteRenderer(BaseRenderer):
        def render(self, catalog: ProjectCatalog, output_path: str) -> None:
            pass

    renderer = ConcreteRenderer()
    renderer.render(ProjectCatalog(), "dummy")


def test_traceability_tags_present():
    """Verify reflection check ensuring all abstract interfaces and methods contain traceability tags."""
    # Check BaseParser docstring
    assert BaseParser.__doc__ is not None
    assert "Satisfies REQ-FUN-02" in BaseParser.__doc__

    # Check BaseParser.parse docstring
    assert BaseParser.parse.__doc__ is not None
    assert "Satisfies REQ-FUN-02" in BaseParser.parse.__doc__

    # Check BaseRenderer docstring
    assert BaseRenderer.__doc__ is not None
    assert "Satisfies REQ-FUN-03" in BaseRenderer.__doc__

    # Check BaseRenderer.render docstring
    assert BaseRenderer.render.__doc__ is not None
    assert "Satisfies REQ-FUN-03" in BaseRenderer.render.__doc__

    # Check Exceptions docstrings
    assert ParserError.__doc__ is not None
    assert "Satisfies REQ-FUN-02" in ParserError.__doc__

    assert RendererError.__doc__ is not None
    assert "Satisfies REQ-FUN-03" in RendererError.__doc__
