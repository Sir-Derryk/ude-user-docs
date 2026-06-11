# engine/tests/test_models.py
# All documentation, docstrings, and code comments are strictly in English.

import pytest
from pydantic import ValidationError
from ude.models import ProjectCatalog, NamespaceEntity, ClassEntity, MethodEntity, ParameterField

def test_valid_project_catalog_construction():
    """Verify that a valid ProjectCatalog object can be constructed with nested objects."""
    catalog = ProjectCatalog(
        namespaces=[
            NamespaceEntity(
                name="MyNamespace",
                classes=[
                    ClassEntity(
                        name="MyClass",
                        fully_qualified_name="MyNamespace::MyClass",
                        docstring="A simple C++ class for demonstration.",
                        methods=[
                            MethodEntity(
                                name="doSomething",
                                signature="void doSomething(int x)",
                                parameters=[
                                    ParameterField(
                                        name="x",
                                        type="int",
                                        description="An integer parameter."
                                    )
                                ],
                                return_type="void",
                                docstring="Performs a useful action."
                            )
                        ],
                        fields=["m_id"]
                    )
                ]
            )
        ]
    )
    
    assert len(catalog.namespaces) == 1
    assert catalog.namespaces[0].name == "MyNamespace"
    assert len(catalog.namespaces[0].classes) == 1
    
    class_entity = catalog.namespaces[0].classes[0]
    assert class_entity.name == "MyClass"
    assert class_entity.fully_qualified_name == "MyNamespace::MyClass"
    assert len(class_entity.methods) == 1
    assert class_entity.fields == ["m_id"]
    
    method = class_entity.methods[0]
    assert method.name == "doSomething"
    assert len(method.parameters) == 1
    assert method.parameters[0].name == "x"

def test_invalid_data_types_trigger_validation_error():
    """Verify that invalid data types trigger a pydantic.ValidationError."""
    # Attempting to construct ClassEntity with an integer for fully_qualified_name (which expects a string)
    with pytest.raises(ValidationError) as exc_info:
        ClassEntity(
            name="MyClass",
            fully_qualified_name=12345,  # Invalid: integer instead of string
            docstring="A class with invalid attributes"
        )
    
    assert "fully_qualified_name" in str(exc_info.value)
