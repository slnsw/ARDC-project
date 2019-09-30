"""Module for parsing and loading Alto XML files.

Supports alto schema 2.0 http://www.loc.gov/standards/alto/v2/alto-2-0.xsd
"""

import os
import xml.etree.ElementTree as ET
from typing import List


_ALTO_ROOT_NS = '{http://www.loc.gov/standards/alto/ns-v3#}'

_ALTO_NS = {
    'alto': 'http://www.loc.gov/standards/alto/ns-v3#',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


class AltoFile:
    """Encapsulates a single alto file."""

    def __str__(self) -> str:
        """Return file path of alto file."""
        return self._file_path

    def __init__(self, file_path: str) -> None:
        """Initialise AltoFile with file_path."""
        self._file_path = file_path
        self._load_file()
        self._parse_alto()

    def _load_file(self) -> None:
        """Open file and load xml tree."""
        for prefix, uri in _ALTO_NS.items():
            ET.register_namespace(prefix, uri)

        tree = ET.parse(self._file_path)
        self._root = tree.getroot()

    def _parse_alto(self) -> None:
        """Load description, styles and layout with data from alto file."""
        self._parse_description()
        self._parse_styles()
        self._parse_layout()

    def _parse_description(self) -> None:
        """Parse description section."""
        self.description = Description(self._root.find("./{root_ns}Description".format(root_ns=_ALTO_ROOT_NS)))

    def _parse_styles(self) -> None:
        """Parse styles section."""
        self.styles = Styles(self._root.find("./{root_ns}Styles".format(root_ns=_ALTO_ROOT_NS)))

    def _parse_layout(self) -> None:
        """Parse layout section."""
        self.layout = Layout(self._root.find("./{root_ns}Layout".format(root_ns=_ALTO_ROOT_NS)))


class AltoFactory:
    """Creates AltoFile instances from alto xml files."""

    def __init__(self, folder_path: str) -> None:
        """Constructor."""
        self._folder_path = folder_path

    def load_files(self, file_names: List[str]) -> List[AltoFile]:
        """Load AltoFile instances."""
        return [AltoFile(os.path.join(self._folder_path, file_name)) for file_name in file_names
                if os.path.isfile(os.path.join(self._folder_path, file_name))]


class Description:
    """Describes general settings of the alto file like measurement units and metadata."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise Description."""
        self._element = element

        measurement_unit_element = element.find('{root_ns}MeasurementUnit'.format(root_ns=_ALTO_ROOT_NS))
        if measurement_unit_element is not None:
            self.measurement_unit = measurement_unit_element.text

        source_image_information_element = element.find('{root_ns}sourceImageInformation'.format(root_ns=_ALTO_ROOT_NS))
        if source_image_information_element is not None:
            self.source_image_information = SourceImageInformation(source_image_information_element)

        self.ocr_processing = None


class SourceImageInformation:
    """Information to identify the image file from which the OCR text was created.."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise source image information."""
        self._element = element

        filename_element = element.find('{root_ns}fileName'.format(root_ns=_ALTO_ROOT_NS))
        if filename_element is not None:
            self.filename = filename_element.text

        self.file_identifiers = []
        file_identifier_elements = element.findall('{root_ns}fileIdentifier'.format(root_ns=_ALTO_ROOT_NS))
        for file_identifier_element in file_identifier_elements:
            self.file_identifiers.append(FileIdentifier(file_identifier_element))


class FileIdentifier:
    """A unique identifier for the image file. This is drawn from MIX."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise file identifier."""
        self._element = element
        self.file_identifier_location = element.attrib['fileIdentifierLocation'] if 'fileIdentifierLocation' in element.attrib else None
        self.text = element.text


class Styles:
    """Styles define properties of layout elements.

    A style defined in a parent element is used as default style for all related children elements."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise Styles."""
        self.text_style = None
        self.paragraph_style = None

        self.text_styles = []
        text_style_elements = element.findall('{root_ns}TextStyle'.format(root_ns=_ALTO_ROOT_NS))
        for text_style_element in text_style_elements:
            self.text_styles.append(TextStyle(text_style_element))

        self.paragraph_styles = []
        paragraph_style_elements = element.findall('{root_ns}ParagraphStyle'.format(root_ns=_ALTO_ROOT_NS))
        for paragraph_style_element in paragraph_style_elements:
            self.paragraph_styles.append(ParagraphStyle(paragraph_style_element))


class TextStyle:
    """A text style defines font properties of text."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise text style."""
        self._element = element
        self.id = element.attrib['ID'] if 'ID' in element.attrib else None
        self.font_family = element.attrib['FONTFAMILY'] if 'FONTFAMILY' in element.attrib else None
        self.font_type = element.attrib['FONTTYPE'] if 'FONTTYPE' in element.attrib else None
        self.font_width = element.attrib['FONTWIDTH'] if 'FONTWIDTH' in element.attrib else None
        self.font_size = element.attrib['FONTSIZE'] if 'FONTSIZE' in element.attrib else None
        self.font_color = element.attrib['FONTCOLOR'] if 'FONTCOLOR' in element.attrib else None
        self.font_style = element.attrib['FONTSTYLE'] if 'FONTSTYLE' in element.attrib else None


class ParagraphStyle:
    """A paragraph style defines formatting properties of text blocks."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise paragraph style."""
        self._element = element
        self.id = element.attrib['ID'] if 'ID' in element.attrib else None
        self.align = element.attrib['ALIGN'] if 'ALIGN' in element.attrib else None
        self.left = element.attrib['LEFT'] if 'LEFT' in element.attrib else None
        self.right = element.attrib['RIGHT'] if 'RIGHT' in element.attrib else None
        self.linespace = element.attrib['LINESPACE'] if 'LINESPACE' in element.attrib else None
        self.firstline = element.attrib['FIRSTLINE'] if 'FIRSTLINE' in element.attrib else None


class Layout:
    """The root layout element."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise Layout."""
        self._element = element
        self.stylerefs = element.attrib['STYLEREFS'] if 'STYLEREFS' in element.attrib else None
        self.pages = []
        self._parse_pages()

    def _parse_pages(self) -> None:
        for child_element in self._element:
            self.pages.append(Page(child_element))


class Page:
    """One page of a book or journal."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise Page."""
        self._element = element
        self.id = element.attrib['ID'] if 'ID' in element.attrib else None
        self.page_class = element.attrib['PAGE_CLASS'] if 'PAGE_CLASS' in element.attrib else None
        self.stylerefs = element.attrib['STYLEREFS'] if 'STYLEREFS' in element.attrib else None
        self.height = element.attrib['HEIGHT'] if 'HEIGHT' in element.attrib else None
        self.width = element.attrib['WIDTH'] if 'WIDTH' in element.attrib else None
        self.physical_img_nr = element.attrib['PHSYSICAL_IMG_NR'] if 'PHSYSICAL_IMG_NR' in element.attrib else None
        self.printed_img_nr = element.attrib['PRINTED_IMG_NR'] if 'PRINTED_IMG_NR' in element.attrib else None
        self.quality = element.attrib['QUALITY'] if 'QUALITY' in element.attrib else None
        self.quality_detail = element.attrib['QUALITY_DETAIL'] if 'QUALITY_DETAIL' in element.attrib else None
        self.position = element.attrib['POSITION'] if 'POSITION' in element.attrib else None
        self.processing = element.attrib['PROCESSING'] if 'PROCESSING' in element.attrib else None
        self.accuracy = element.attrib['ACCURACY'] if 'ACCURACY' in element.attrib else None
        self.pc = element.attrib['PC'] if 'PC' in element.attrib else None
        self._parse_page_spaces()

    def _parse_page_spaces(self) -> None:
        self.top_margin = TopMargin(self._element.find("./{root_ns}TopMargin".format(root_ns=_ALTO_ROOT_NS)))
        self.left_margin = LeftMargin(self._element.find("./{root_ns}LeftMargin".format(root_ns=_ALTO_ROOT_NS)))
        self.right_margin = RightMargin(self._element.find("./{root_ns}RightMargin".format(root_ns=_ALTO_ROOT_NS)))
        self.bottom_margin = BottomMargin(self._element.find("./{root_ns}BottomMargin".format(root_ns=_ALTO_ROOT_NS)))
        self.print_space = PrintSpace(self._element.find("./{root_ns}PrintSpace".format(root_ns=_ALTO_ROOT_NS)))


class PageSpaceType:
    """A region on a page."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise page space."""
        self._element = element
        self.id = element.attrib['ID'] if 'ID' in element.attrib else None
        self.stylerefs = element.attrib['STYLEREFS'] if 'STYLEREFS' in element.attrib else None
        self.hpos = element.attrib['HPOS'] if 'HPOS' in element.attrib else None
        self.vpos = element.attrib['VPOS'] if 'VPOS' in element.attrib else None
        self.width = element.attrib['WIDTH'] if 'WIDTH' in element.attrib else None
        self.height = element.attrib['HEIGHT'] if 'HEIGHT' in element.attrib else None
        self._parse_blocks()
        self.i = 0
        self.n = len(self.blocks)

    def _parse_blocks(self) -> None:
        factory = BlockFactory(self._element)
        self.blocks = factory.load_blocks()

    def __iter__(self):
        """Iterate implementation."""
        return self

    def __next__(self):
        """Iterate implementation."""
        if self.i < self.n:
            self.i += 1
            return self.blocks[self.i - 1]
        else:
            raise StopIteration


class TopMargin(PageSpaceType):
    """The area between the top line of print and the upper edge of the leaf.

    It may contain page number or running title."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise top margin."""
        super().__init__(element)


class LeftMargin(PageSpaceType):
    """The area between the printspace and the left border of a page. May contain margin notes."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise left margin."""
        super().__init__(element)


class RightMargin(PageSpaceType):
    """The area between the printspace and the right border of a page. May contain margin notes."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise right margin."""
        super().__init__(element)


class BottomMargin(PageSpaceType):
    """The area between the bottom line of letterpress or writing and the bottom edge of the leaf.

    It may contain a page number, a signature number or a catch word."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise bottom margin."""
        super().__init__(element)


class PrintSpace(PageSpaceType):
    """Rectangle covering the printed area of a page. Page number and running title are not part of the print space."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise print space."""
        super().__init__(element)


class BlockType():
    """Base type for any kind of block on the page."""

    def __init__(self, element: ET.Element) -> None:
        """Constructor."""
        self._element = element
        self.id = element.attrib['ID'] if 'ID' in element.attrib else None
        self.stylerefs = element.attrib['STYLEREFS'] if 'STYLEREFS' in element.attrib else None
        self.hpos = element.attrib['HPOS'] if 'HPOS' in element.attrib else None
        self.vpos = element.attrib['VPOS'] if 'VPOS' in element.attrib else None
        self.width = element.attrib['WIDTH'] if 'WIDTH' in element.attrib else None
        self.height = element.attrib['HEIGHT'] if 'HEIGHT' in element.attrib else None
        self.rotation = element.attrib['ROTATION'] if 'ROTATION' in element.attrib else None
        self._parse_shape()

    def _parse_shape(self) -> None:
        factory = ShapeFactory(self._element)
        self.shape = factory.load_shape()


class ComposedBlock(BlockType):
    """A block that consists of other blocks."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise composed block."""
        super().__init__(element)
        self.type = element.attrib['TYPE'] if 'TYPE' in element.attrib else None
        self.fileid = element.attrib['FILEID'] if 'FILEID' in element.attrib else None
        self._parse_blocks()
        self.i = 0
        self.n = len(self.blocks)

    def _parse_blocks(self) -> None:
        factory = BlockFactory(self._element)
        self.blocks = factory.load_blocks()

    def __iter__(self):
        """Iterate implementation."""
        return self

    def __next__(self):
        """Iterate implementation."""
        if self.i < self.n:
            self.i += 1
            return self.blocks[self.i - 1]
        else:
            raise StopIteration


class TextBlock(BlockType):
    """A block of text."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise text block."""
        super().__init__(element)
        self.language = element.attrib['LANGUAGE'] if 'LANGUAGE' in element.attrib else None
        self.text_lines = []
        self._parse_text_lines()
        self.i = 0
        self.n = len(self.text_lines)

    def _parse_text_lines(self) -> None:
        for child in self._element:
            if child.tag == '{root_ns}TextLine'.format(root_ns=_ALTO_ROOT_NS):
                self.text_lines.append(TextLine(child))

    def __iter__(self):
        """Iterate implementation."""
        return self

    def __next__(self):
        """Iterate implementation."""
        if self.i < self.n:
            self.i += 1
            return self.text_lines[self.i - 1]
        else:
            raise StopIteration


class Illustration(BlockType):
    """A picture or image."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise illustration block."""
        super().__init__(element)
        self.type = element.attrib['TYPE'] if 'TYPE' in element.attrib else None
        self.fileid = element.attrib['FILEID'] if 'FILEID' in element.attrib else None


class GraphicalElement(BlockType):
    """A graphic used to separate blocks. Usually a line or rectangle."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise graphical element block."""
        super().__init__(element)


class BlockFactory():
    """Creates Block instances."""

    def __init__(self, element: ET.Element) -> None:
        """Constructor."""
        self._element = element

    def load_blocks(self) -> List[BlockType]:
        """Load BlockType instances."""
        blocks = []
        for block in self._element:
            if block.tag == '{root_ns}ComposedBlock'.format(root_ns=_ALTO_ROOT_NS):
                blocks.append(ComposedBlock(block))
            elif block.tag == '{root_ns}TextBlock'.format(root_ns=_ALTO_ROOT_NS):
                blocks.append(TextBlock(block))
            elif block.tag == '{root_ns}Illustration'.format(root_ns=_ALTO_ROOT_NS):
                blocks.append(Illustration(block))
            elif block.tag == '{root_ns}GraphicalElement'.format(root_ns=_ALTO_ROOT_NS):
                blocks.append(GraphicalElement(block))
        return blocks


class ShapeType():
    """Describes the bounding shape of a block, if it is not rectangular."""

    def __init__(self, element: ET.Element) -> None:
        """Constructor."""
        self._element = element


class ShapeFactory():
    """Creates ShapeType instances."""

    def __init__(self, element: ET.Element) -> None:
        """Constructor."""
        self._element = element

    def load_shape(self) -> ShapeType:
        """Load a ShapeType instance."""
        for child in self._element:
            if child.tag == '{root_ns}Polygon'.format(root_ns=_ALTO_ROOT_NS):
                return(Polygon(child))
            elif child.tag == '{root_ns}Ellipse'.format(root_ns=_ALTO_ROOT_NS):
                return(Ellipse(child))
            elif child.tag == '{root_ns}Circle'.format(root_ns=_ALTO_ROOT_NS):
                return(Circle(child))
        return None


class Polygon(ShapeType):
    """A polygon shape."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise polygon."""
        super().__init__(element)
        self.points = element.attrib['POINTS'] if 'POINTS' in element.attrib else None


class Ellipse(ShapeType):
    """An ellipse shape."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise ellipse."""
        super().__init__(element)
        self.hpos = element.attrib['HPOS'] if 'HPOS' in element.attrib else None
        self.vpos = element.attrib['VPOS'] if 'VPOS' in element.attrib else None
        self.hlength = element.attrib['HLENGTH'] if 'HLENGTH' in element.attrib else None
        self.vlength = element.attrib['VLENGTH'] if 'VLENGTH' in element.attrib else None


class Circle(ShapeType):
    """A circle shape."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise circle."""
        super().__init__(element)
        self.hpos = element.attrib['HPOS'] if 'HPOS' in element.attrib else None
        self.vpos = element.attrib['VPOS'] if 'VPOS' in element.attrib else None
        self.radius = element.attrib['RADIUS'] if 'RADIUS' in element.attrib else None


class TextLine():
    """A single line of text."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise text line."""
        self._element = element
        self.id = element.attrib['ID'] if 'ID' in element.attrib else None
        self.stylerefs = element.attrib['STYLEREFS'] if 'STYLEREFS' in element.attrib else None
        self.hpos = element.attrib['HPOS'] if 'HPOS' in element.attrib else None
        self.vpos = element.attrib['VPOS'] if 'VPOS' in element.attrib else None
        self.width = element.attrib['WIDTH'] if 'WIDTH' in element.attrib else None
        self.height = element.attrib['HEIGHT'] if 'HEIGHT' in element.attrib else None
        self.baseline = element.attrib['BASELINE'] if 'BASELINE' in element.attrib else None
        self.cs = element.attrib['CS'] if 'CS' in element.attrib else None
        self._parse_line_elements()
        self.i = 0
        self.n = len(self.line_parts)

    def _parse_line_elements(self) -> None:
        factory = LinePartFactory(self._element)
        self.line_parts = factory.load_parts()

    def __iter__(self):
        """Iterate implementation."""
        return self

    def __next__(self):
        """Iterate implementation."""
        if self.i < self.n:
            self.i += 1
            return self.line_parts[self.i - 1]
        else:
            raise StopIteration


class LinePart():
    """Abstract class for elements contained in a line."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise line element."""
        self._element = element


class String(LinePart):
    """A sequence of chars. Strings are separated by white spaces or hyphenation chars."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise string."""
        super().__init__(element)
        self.id = element.attrib['ID'] if 'ID' in element.attrib else None
        self.hpos = element.attrib['HPOS'] if 'HPOS' in element.attrib else None
        self.vpos = element.attrib['VPOS'] if 'VPOS' in element.attrib else None
        self.width = element.attrib['WIDTH'] if 'WIDTH' in element.attrib else None
        self.height = element.attrib['HEIGHT'] if 'HEIGHT' in element.attrib else None
        self.content = element.attrib['CONTENT'] if 'CONTENT' in element.attrib else None
        self.subs_content = element.attrib['SUBS_CONTENT'] if 'SUBS_CONTENT' in element.attrib else None
        self.stylerefs = element.attrib['STYLEREFS'] if 'STYLEREFS' in element.attrib else None
        self.style = element.attrib['STYLE'] if 'STYLE' in element.attrib else None
        self.subs_type = element.attrib['SUBS_TYPE'] if 'SUBS_TYPE' in element.attrib else None
        self.wc = element.attrib['WC'] if 'WC' in element.attrib else None
        self.cc = element.attrib['CC'] if 'CC' in element.attrib else None
        self.alternatives = []
        alternative_elements = element.findall('{root_ns}ALTERNATIVE'.format(root_ns=_ALTO_ROOT_NS))
        for alternative_element in alternative_elements:
            self.alternatives.append(Alternative(alternative_element))


class Alternative():
    """Any alternative for the word."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise alternativer."""
        self.purpose = element.attrib['PURPOSE'] if 'PURPOSE' in element.attrib else None
        self.text = element.text


class Sp(LinePart):
    """A white space."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise space."""
        super().__init__(element)
        self.id = element.attrib['ID'] if 'ID' in element.attrib else None
        self.hpos = element.attrib['HPOS'] if 'HPOS' in element.attrib else None
        self.vpos = element.attrib['VPOS'] if 'VPOS' in element.attrib else None
        self.width = element.attrib['WIDTH'] if 'WIDTH' in element.attrib else None


class Hyp(LinePart):
    """A hyphenation char. Can appear only at the end of a line."""

    def __init__(self, element: ET.Element) -> None:
        """Initialise hyphen."""
        super().__init__(element)
        self.hpos = element.attrib['HPOS'] if 'HPOS' in element.attrib else None
        self.vpos = element.attrib['VPOS'] if 'VPOS' in element.attrib else None
        self.width = element.attrib['WIDTH'] if 'WIDTH' in element.attrib else None
        self.content = element.attrib['CONTENT'] if 'CONTENT' in element.attrib else None


class LinePartFactory():
    """Creates LinePart instances."""

    def __init__(self, element: ET.Element) -> None:
        """Constructor."""
        self._element = element

    def load_parts(self) -> List[LinePart]:
        """Load LinePart instances."""
        line_parts = []
        for line_part in self._element:
            if line_part.tag == '{root_ns}String'.format(root_ns=_ALTO_ROOT_NS):
                line_parts.append(String(line_part))
            elif line_part.tag == '{root_ns}SP'.format(root_ns=_ALTO_ROOT_NS):
                line_parts.append(Sp(line_part))
            elif line_part.tag == '{root_ns}HYP'.format(root_ns=_ALTO_ROOT_NS):
                line_parts.append(Hyp(line_part))
        return line_parts


# TODO open up repo and add module to PyPi
# TODO more unittests to get 100% code coverage
# TODO add validation, should be optional on initialisation
# TODO parse ocr_processing
