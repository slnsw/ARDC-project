import typing
import xml.etree.ElementTree as ET
from xmljson import gdata, yahoo
from lxml import objectify, etree
from collections import OrderedDict


def load_xml(data: str) -> ET.Element:
    s = data.encode('utf-8')
    utf8_parser = etree.XMLParser(encoding='utf-8')
    return objectify.fromstring(s, parser=utf8_parser)


def load_xml_file(path: str, iterate: bool = True) -> ET.Element:
    if iterate:
        tree = etree.iterparse(path, recover=True)
    else:
        tree = etree.parse(path)
    return tree


def xval(root: ET.Element, xpath: str, namespaces: dict = None, sep: str = ' ') -> str:
    namespaces = namespaces if namespaces else {}
    els_xpath = etree.XPath(xpath, namespaces=namespaces)
    els = els_xpath(root)
    texts = []
    for el in els:
        if el is None:
            pass
        elif isinstance(el, str):
            texts.append(el)
        else:
            text = el.text
            if text:
                texts.append(text)
    return sep.join(texts).strip() if type(sep) is str else texts


def xels(root: ET.Element, xpath: str, namespaces: dict = None) -> typing.List[ET.Element]:
    namespaces = namespaces if namespaces else {}
    els_xpath = etree.XPath(xpath, namespaces=namespaces)
    els = els_xpath(root)
    return els


def xel(root: ET.Element, xpath: str, namespaces: dict = None) -> typing.Optional[ET.Element]:
    els = xels(root=root, xpath=xpath, namespaces=namespaces)
    return els[0] if len(els) else None


def json_xml(data: dict) -> ET.ElementTree:
    xml_data = gdata.etree(data)
    return xml_data


def xml_str(root: ET.Element, encoding: str = 'utf-8'):
    xml_str = ET.tostring(root, encoding=encoding).decode(encoding)
    return xml_str


def xml_json(data: ET.Element) -> dict:
    json_data = yahoo.data(data)
    return json_data


def json_remove_dots(data):
    if type(data) is list:
        for key in list(range(len(data))):
            data[key] = json_remove_dots(data[key])
    elif type(data) is dict or type(data) is OrderedDict:
        for key in list(data.keys()):
            key2 = key
            if type(key) is str and '.' in key:
                key2 = key.replace('.', '__')  # '\uff0E'
                data[key2] = data[key]
                del data[key]
            data[key2] = json_remove_dots(data[key2])
    return data
