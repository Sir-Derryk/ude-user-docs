# engine/ude/parsers/doxygen.py
# All documentation, docstrings, and code comments are strictly in English.

import os
import re
from typing import List, Optional, Dict
import xml.etree.ElementTree as ET
from pathlib import Path

from ude.interfaces import BaseParser, ParserError
from ude.models import ProjectCatalog, NamespaceEntity, ClassEntity, MethodEntity, ParameterField


def strip_export_macros(text: Optional[str], macros: Optional[List[str]] = None) -> Optional[str]:
    """Strips compiler-specific export macros from the provided string.

    Args:
        text: The input text to process.
        macros: Custom list of macros to strip. Defaults to ['NWDBEXPORT', 'MAPEXPORT'].

    Returns:
        The processed string with macros removed and normalized whitespace.

    Satisfies REQ-FUN-19
    """
    if text is None:
        return None
    if macros is None:
        macros = ["NWDBEXPORT", "MAPEXPORT"]
    for macro in macros:
        text = re.sub(rf"\b{macro}\b", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class DoxygenXmlParser(BaseParser):
    """Doxygen XML parser mapping nested C++, C#, Java, and Python structures.

    This parser ingests raw metrics and code structures from an index.xml catalog and
    resolves the complete document graph into a language-agnostic Intermediate Representation.

    Satisfies REQ-FUN-02, REQ-FUN-19, REQ-FUN-20
    """

    def __init__(self, exclude_swig_internals: bool = False, **kwargs):
        """Initializes the DoxygenXmlParser with configuration flags.

        Args:
            exclude_swig_internals: If True, filters out SWIG specific members and fields.
            **kwargs: Additional configuration parameters.

        Satisfies REQ-FUN-02, REQ-FUN-20
        """
        self.exclude_swig_internals = exclude_swig_internals
        self.swig_fields = {"swigCPtr", "swigCMemOwn"}
        self.swig_methods = {"Dispose", "getCPtr"}

    def _filter_exclusions(self, xml_text: str) -> str:
        """Filters out exclusion ranges from the raw XML text.

        Removes anything between DOM-IGNORE-BEGIN/DOM-IGNORE-END and
        between \\cond/\\endcond or @cond/@endcond.

        Args:
            xml_text: Raw XML string content.

        Returns:
            XML string content with excluded blocks stripped.
        """
        # Handle DOM-IGNORE blocks (with or without XML comments)
        pattern_ignore = r"(?:<!--\s*)?DOM-IGNORE-BEGIN(?:\s*-->)?.*?(?:<!--\s*)?DOM-IGNORE-END(?:\s*-->)?"
        xml_text = re.sub(pattern_ignore, "", xml_text, flags=re.DOTALL)

        # Handle \cond and @cond blocks (with or without XML comments)
        pattern_cond = r"(?:<!--\s*)?[\\@]cond(?:\s*-->)?.*?(?:<!--\s*)?[\\@]endcond(?:\s*-->)?"
        xml_text = re.sub(pattern_cond, "", xml_text, flags=re.DOTALL)

        return xml_text

    def parse(self, input_path: str) -> ProjectCatalog:
        """Parses the input directory containing Doxygen XML files and builds the ProjectCatalog.

        Args:
            input_path: Path to the target Doxygen XML directory containing index.xml.

        Returns:
            A populated ProjectCatalog representing the code structures.

        Raises:
            ParserError: If the input path is invalid, missing files, or contains malformed XML.

        Satisfies REQ-FUN-02
        """
        path = Path(input_path)
        if not path.exists():
            raise ParserError(f"Input path does not exist: {input_path}")

        index_file = path / "index.xml" if path.is_dir() else path
        if not index_file.exists() or index_file.name != "index.xml":
            raise ParserError(f"Doxygen index file 'index.xml' not found in: {input_path}")

        try:
            content = index_file.read_text(encoding="utf-8")
            filtered_content = self._filter_exclusions(content)
            root = ET.fromstring(filtered_content)
        except ET.ParseError as e:
            raise ParserError(f"Malformed index.xml: {e}") from e

        # Gather compounds
        compounds = root.findall("compound")
        namespace_dict: Dict[str, List[ClassEntity]] = {}

        for compound in compounds:
            kind = compound.get("kind")
            refid = compound.get("refid")
            if kind not in ("class", "struct", "interface"):
                continue

            # Locate the compound XML file
            compound_file = index_file.parent / f"{refid}.xml"
            if not compound_file.exists():
                # Scan all XML files in the directory to find compounddef with matching id
                found = False
                for f in index_file.parent.glob("*.xml"):
                    if f.name == "index.xml":
                        continue
                    try:
                        c_content = f.read_text(encoding="utf-8")
                        c_filtered = self._filter_exclusions(c_content)
                        c_root = ET.fromstring(c_filtered)
                        compounddef = c_root.find("compounddef")
                        if compounddef is not None and compounddef.get("id") == refid:
                            compound_file = f
                            found = True
                            break
                    except Exception:
                        continue
                if not found:
                    continue

            # Parse compound definition
            try:
                class_entity = self._parse_compound_file(compound_file)
                if class_entity is not None:
                    # Determine namespace from fully qualified name
                    raw_name = class_entity.fully_qualified_name
                    # Parse name
                    namespace_path, class_name, fqn = self._parse_compound_name(raw_name)
                    
                    # Update class entity name and fqn
                    class_entity.name = class_name
                    class_entity.fully_qualified_name = fqn
                    
                    if namespace_path not in namespace_dict:
                        namespace_dict[namespace_path] = []
                    namespace_dict[namespace_path].append(class_entity)
            except Exception as e:
                raise ParserError(f"Error parsing compound file {compound_file}: {e}") from e

        # Build ProjectCatalog
        namespaces = []
        for ns_name, classes in namespace_dict.items():
            namespaces.append(NamespaceEntity(name=ns_name, classes=classes))

        return ProjectCatalog(namespaces=namespaces)

    def _parse_compound_name(self, compound_name: str) -> tuple[str, str, str]:
        """Parses compound name, normalizing separators to '::' and stripping macros.

        Args:
            compound_name: Raw compound name from XML.

        Returns:
            A tuple of (namespace_path, class_name, fully_qualified_name).

        Satisfies REQ-FUN-02, REQ-FUN-19
        """
        # Replace . with ::
        normalized = compound_name.replace(".", "::")
        normalized = strip_export_macros(normalized)

        # Handle templates correctly when parsing namespaces.
        # Template brackets < > can contain double colons (e.g., Traits<Type::Value>).
        # We must only split by :: outside of template brackets!
        parts = []
        bracket_level = 0
        current_part = []
        
        i = 0
        n = len(normalized)
        while i < n:
            char = normalized[i]
            if char == "<":
                bracket_level += 1
                current_part.append(char)
                i += 1
            elif char == ">":
                bracket_level -= 1
                current_part.append(char)
                i += 1
            elif char == ":" and i + 1 < n and normalized[i + 1] == ":" and bracket_level == 0:
                parts.append("".join(current_part))
                current_part = []
                i += 2
            else:
                current_part.append(char)
                i += 1
        parts.append("".join(current_part))

        class_name = parts[-1]
        if len(parts) > 1:
            namespace_path = "::".join(parts[:-1])
            fully_qualified_name = f"{namespace_path}::{class_name}"
        else:
            namespace_path = ""
            fully_qualified_name = class_name

        return namespace_path, class_name, fully_qualified_name

    def _parse_compound_file(self, compound_file: Path) -> Optional[ClassEntity]:
        """Parses an individual class XML definition file.

        Args:
            compound_file: Path to the XML file.

        Returns:
            A populated ClassEntity, or None.

        Satisfies REQ-FUN-02, REQ-FUN-19, REQ-FUN-20
        """
        content = compound_file.read_text(encoding="utf-8")
        filtered_content = self._filter_exclusions(content)
        try:
            root = ET.fromstring(filtered_content)
        except ET.ParseError as e:
            raise ParserError(f"Malformed compound file {compound_file}: {e}") from e

        compounddef = root.find("compounddef")
        if compounddef is None:
            return None

        raw_fqn = compounddef.findtext("compoundname", "").strip()
        entity_kind = compounddef.get("kind", "class")
        docstring = self._extract_docstring(compounddef)
        if docstring and ("@internal" in docstring or "\\internal" in docstring):
            return None

        methods: List[MethodEntity] = []
        fields: List[str] = []

        # Iterate over sectiondefs
        for sectiondef in compounddef.findall("sectiondef"):
            for memberdef in sectiondef.findall("memberdef"):
                kind = memberdef.get("kind")
                member_name = memberdef.findtext("name", "").strip()

                if kind == "function":
                    # Check SWIG filter
                    if self.exclude_swig_internals and member_name in self.swig_methods:
                        continue

                    method_entity = self._parse_method(memberdef)
                    if method_entity is not None:
                        if method_entity.docstring and ("@internal" in method_entity.docstring or "\\internal" in method_entity.docstring):
                            continue
                        methods.append(method_entity)

                elif kind in ("variable", "typedef"):
                    # Check SWIG filter
                    if self.exclude_swig_internals and (
                        member_name in self.swig_fields or any(s in member_name for s in self.swig_fields)
                    ):
                        continue

                    field_docstring = self._extract_docstring(memberdef)
                    if field_docstring and ("@internal" in field_docstring or "\\internal" in field_docstring):
                        continue

                    field_text = self._parse_field(memberdef)
                    if field_text:
                        fields.append(field_text)

        return ClassEntity(
            name=raw_fqn,  # updated later in parse()
            fully_qualified_name=raw_fqn,
            entity_type=entity_kind,
            docstring=docstring,
            methods=methods,
            fields=fields,
        )

    def _parse_method(self, memberdef: ET.Element) -> Optional[MethodEntity]:
        """Parses a memberdef of kind function into a MethodEntity.

        Args:
            memberdef: The XML element for the memberdef.

        Returns:
            A populated MethodEntity.

        Satisfies REQ-FUN-02, REQ-FUN-19
        """
        name = memberdef.findtext("name", "").strip()
        
        # Attributes
        is_static = memberdef.get("static") == "yes"
        is_virtual = memberdef.get("virt") in ("virtual", "pure-virtual")

        # Type (Return type)
        type_elem = memberdef.find("type")
        if type_elem is not None:
            return_type = "".join(type_elem.itertext()).strip()
        else:
            return_type = ""
        return_type = strip_export_macros(return_type) or ""

        # Docstring
        docstring = self._extract_docstring(memberdef)

        # Parameters
        parameters: List[ParameterField] = []
        for param in memberdef.findall("param"):
            p_type_elem = param.find("type")
            p_type = "".join(p_type_elem.itertext()).strip() if p_type_elem is not None else ""
            p_type = strip_export_macros(p_type) or ""
            
            p_name = param.findtext("declname", "").strip()
            parameters.append(ParameterField(name=p_name, type=p_type))

        # Signature
        def_elem = memberdef.find("definition")
        args_elem = memberdef.find("argsstring")
        
        def_text = "".join(def_elem.itertext()).strip() if def_elem is not None else ""
        args_text = "".join(args_elem.itertext()).strip() if args_elem is not None else ""
        
        def_text = strip_export_macros(def_text) or ""
        args_text = strip_export_macros(args_text) or ""

        if def_text:
            signature = f"{def_text}{args_text}"
        else:
            # Fallback
            param_str = ", ".join(f"{p.type} {p.name}".strip() for p in parameters)
            prefix = "static " if is_static else ""
            signature = f"{prefix}{return_type} {name}({param_str})"
            signature = re.sub(r"\s+", " ", signature).strip()

        return MethodEntity(
            name=name,
            signature=signature,
            parameters=parameters,
            return_type=return_type,
            docstring=docstring,
            is_static=is_static,
            is_virtual=is_virtual,
        )

    def _parse_field(self, memberdef: ET.Element) -> Optional[str]:
        """Parses a memberdef of kind variable or typedef into a field string.

        Args:
            memberdef: The XML element for the memberdef.

        Returns:
            A formatted string representing the field.

        Satisfies REQ-FUN-02, REQ-FUN-19
        """
        def_elem = memberdef.find("definition")
        if def_elem is not None:
            def_text = "".join(def_elem.itertext()).strip()
            return strip_export_macros(def_text)

        type_elem = memberdef.find("type")
        name_elem = memberdef.find("name")
        if type_elem is not None and name_elem is not None:
            t_text = "".join(type_elem.itertext()).strip()
            n_text = name_elem.text.strip() if name_elem.text else ""
            field_text = f"{t_text} {n_text}".strip()
            return strip_export_macros(field_text)

        return None

    def _extract_docstring(self, element: ET.Element) -> Optional[str]:
        """Extracts and cleans the docstring from brief and detailed descriptions.

        Args:
            element: The XML element containing descriptions.

        Returns:
            The combined and cleaned docstring, or None.

        Satisfies REQ-FUN-02
        """
        brief_elem = element.find("briefdescription")
        detail_elem = element.find("detaileddescription")

        parts = []
        for elem in (brief_elem, detail_elem):
            if elem is not None:
                paras = elem.findall(".//para")
                for para in paras:
                    text = "".join(para.itertext()).strip()
                    if text:
                        parts.append(text)

        if parts:
            return "\n\n".join(parts)
        return None
