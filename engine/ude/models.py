# engine/ude/models.py
# All documentation, docstrings, and code comments are strictly in English.

from typing import List, Optional
from pydantic import BaseModel, Field

class ParameterField(BaseModel):
    """Represents a method parameter's attributes."""
    name: str
    type: str
    description: Optional[str] = None

class MethodEntity(BaseModel):
    """Represents functions, methods, and constructors."""
    name: str
    signature: str
    parameters: List[ParameterField] = Field(default_factory=list)
    return_type: str
    docstring: Optional[str] = None
    is_static: bool = False
    is_virtual: bool = False

class ClassEntity(BaseModel):
    """Represents a class, interface, or struct."""
    name: str
    fully_qualified_name: str
    entity_type: str = "class"
    docstring: Optional[str] = None
    methods: List[MethodEntity] = Field(default_factory=list)
    fields: List[str] = Field(default_factory=list)

class NamespaceEntity(BaseModel):
    """Represents a namespace, package, or module scope."""
    name: str
    classes: List[ClassEntity] = Field(default_factory=list)

class ProjectCatalog(BaseModel):
    """Root container representing the language-agnostic Intermediate Representation (IR)."""
    namespaces: List[NamespaceEntity] = Field(default_factory=list)
    metadata: Optional[dict] = Field(default_factory=dict)

