import base64
import collections
import typing
from io import StringIO
import re
import requests
from lxml import etree, objectify
from requests import Session
from zeep import Client, helpers
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport
from xmljson import yahoo
import xml.etree.ElementTree as ET


mets_ns = {
    'mets': 'http://www.loc.gov/METS/',
    'dnx': 'http://www.exlibrisgroup.com/dps/dnx',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'dcterms': 'http://purl.org/dc/terms/',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
}


def xml_json(data, remove_ns=True, preserve_root=False, encoding='utf-8') -> dict:
    if type(data) == str:
        if remove_ns:
            xml_data = ET.iterparse(StringIO(data))
            for _, el in xml_data:
                if '}' in el.tag:
                    el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
            data = ET.tostring(xml_data.root, encoding=encoding).decode(encoding)
        encoded_data = data.encode(encoding)
        # noinspection PyArgumentList
        parser = etree.XMLParser(encoding=encoding, recover=False, huge_tree=True)
        xml_data = objectify.fromstring(encoded_data, parser=parser)
    else:
        xml_data = data
    json_data = yahoo.data(xml_data)
    if type(json_data) == collections.OrderedDict and not preserve_root:
        json_data = json_data.get(list(json_data.keys())[0])
    return json_data


def xval(root: ET.Element, xpath: str, namespaces: dict = None, sep: str = ' ') -> str:
    namespaces = namespaces if namespaces else mets_ns
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
    namespaces = namespaces if namespaces else mets_ns
    els_xpath = etree.XPath(xpath, namespaces=namespaces)
    els = els_xpath(root)
    return els


def xel(root: ET.Element, xpath: str, namespaces: dict = None) -> typing.Optional[ET.Element]:
    els = xels(root=root, xpath=xpath, namespaces=namespaces)
    return els[0] if len(els) else None


class Rosetta(object):
    def __init__(self, api_endpoint: str, api_pds_endpoint: str, api_sru_endpoint: str,
                 api_username: str, api_password: str, api_institude_code: str, api_timeout=600):
        self.api_endpoint = api_endpoint
        self.api_pds_endpoint = api_pds_endpoint
        self.api_src_endpoint = api_sru_endpoint
        self.api_username = api_username
        self.api_password = api_password
        self.api_institute_code = api_institude_code
        self.api_timeout = api_timeout
        self.session = Session()
        auth_data = '%s-institutionCode-%s:%s' % (api_username, api_institude_code, api_password)
        self.session.headers['Authorization'] = base64.b64encode(auth_data.encode('ascii'))
        # self.session.auth = HTTPBasicAuth(api_username, api_password)
        self.client_history = HistoryPlugin()
        self.clients = {}
        self.api_pds_handle = None
        self.last_error_data = None

    def get_ws_url(self, name: str):
        urls = {
            'DepositWebServices': '/dpsws/deposit/DepositWebServices?wsdl',
            'SipWebServices': '/dpsws/repository/SipWebServices?wsdl',
            'IEWebServices': '/dpsws/repository/IEWebServices?wsdl',
            'DataManagerServicesWS': '/dpsws/repository/DataManagerServicesWS?wsdl'
        }
        return self.api_endpoint + urls.get(name)

    def get_client(self, name: str) -> Client:
        if not self.clients.get(name):
            ws_url = self.get_ws_url(name=name)
            transport = Transport(session=self.session, timeout=self.api_timeout, operation_timeout=self.api_timeout)
            client = Client(ws_url, transport=transport, plugins=[self.client_history])
            self.clients[name] = client
        return self.clients[name]

    def get_pds_handle(self):
        if not self.api_pds_handle:
            r = requests.request(method='get', url=self.api_pds_endpoint, params={
                'func': 'login',
                'bor_id': self.api_username,
                'bor_verification': self.api_password,
                'institute': self.api_institute_code
            })
            s = re.search('pds_handle=(?P<pds_handle>\d+)&', r.text)
            if s:
                pds_handle = s.groupdict({}).get('pds_handle')
                self.api_pds_handle = pds_handle
            else:
                s = re.search('<label class="errorMessage">(?P<error_message>.+)</label>', r.text)
                if s:
                    error_message = s.groupdict({}).get('error_message')
                    self.last_error_data = {'message': error_message}
                else:
                    self.last_error_data = {'message': 'Authentication error in PDS'}
        return self.api_pds_handle

    def get_sru_request(self, params: dict):
        r = requests.request(method='get', url=self.api_src_endpoint, params={**{
            'version': '1.2'
        }, **params})
        return r

    def get_sru_response(self, params: dict):
        response = self.get_sru_request(params=params)
        result = xml_json(response.text)
        return result

    def get_sru_searchretrieve_by_sipid(self, sip_id: str):
        data = self.get_sru_response(params={
            'operation': 'searchRetrieve',
            'query': 'IE.dc.identifier=%s' % (sip_id,)
        })
        return data

    def depositws_submit_deposit_activity(self, material_flow_id: str, sub_dir_name: str, producer_id: str) -> dict:
        # https://developers.exlibrisgroup.com/rosetta/apis/DepositWebServices
        # https://exlibrisgroup.github.io/Rosetta.dps-sdk-projects/current/javadoc/com/exlibris/dps/sdk/deposit/DepositWebServices.html#submitDepositActivity-java.lang.String-java.lang.String-java.lang.String-java.lang.String-java.lang.String-
        client = self.get_client(name='DepositWebServices')
        pds_handle = self.get_pds_handle()
        result = {}
        if pds_handle:
            xml_data = client.service.submitDepositActivity(pds_handle, material_flow_id, sub_dir_name, producer_id)
            result = xml_json(xml_data)
        return result

    def sipws_get_sip_status_info(self, sip_id: str) -> dict:
        # https://developers.exlibrisgroup.com/rosetta/apis/SipWebServices
        # https://exlibrisgroup.github.io/Rosetta.dps-sdk-projects/current/javadoc/com/exlibris/dps/sdk/sip/SipWebServices.html#getSIPStatusInfo-java.lang.String-
        client = self.get_client(name='SipWebServices')
        result = client.service.getSIPStatusInfo(sip_id)
        result = helpers.serialize_object(result)
        return result

    def sipws_get_sip_ies(self, sip_id: str) -> typing.List[str]:
        # https://developers.exlibrisgroup.com/rosetta/apis/SipWebServices
        # https://exlibrisgroup.github.io/Rosetta.dps-sdk-projects/current/javadoc/com/exlibris/dps/sdk/sip/SipWebServices.html#getSipIEs-java.lang.String-
        client = self.get_client(name='SipWebServices')
        result = client.service.getSipIEs(sip_id)  # type: str
        ies = None
        if result:
            # Example result: IE1234,
            ies = [ie for ie in result.replace('IE', '').split(',') if ie]
        return ies

    def iews_get_ie(self, ie_id: str, flags: int = 2, raw=False) -> dict:
        # https://developers.exlibrisgroup.com/rosetta/apis/IEWebServices
        # https://exlibrisgroup.github.io/Rosetta.dps-sdk-projects/current/javadoc/com/exlibris/digitool/repository/ifc/IEWebServices.html#getIE-java.lang.String-java.lang.String-java.lang.Long-
        client = self.get_client(name='IEWebServices')
        pds_handle = self.get_pds_handle()
        ie_id = ie_id if isinstance(ie_id, str) else str(ie_id)
        ie_id = ie_id if ie_id.startswith('IE') else 'IE%s' % ie_id
        result = {}
        if pds_handle:
            # by default: flags set to 2, means exclude all the detailed information about the files
            # this code is commented out, it seems there is bug in python-zeep that if XML is way too big
            # the XML is getting cut off, the only way is to get raw response and parse from there
            # xml_data = client.service.getIE(pds_handle, ie_id, flags)
            # result = self.xml_json(xml_data)
            with client.settings(raw_response=True):
                response = client.service.getIE(pds_handle, ie_id, flags)
                encoding = 'utf-8'
                # noinspection PyArgumentList
                parser = etree.XMLParser(encoding=encoding, huge_tree=True)
                xml_data = objectify.fromstring(response.content.decode(), parser=parser)
                xml_raw = xml_data.xpath('//getIE')[0].text
                if not raw:
                    result = xml_json(xml_raw)
                else:
                    # noinspection PyArgumentList
                    parser2 = etree.XMLParser(encoding=encoding, recover=False, huge_tree=True)
                    result = objectify.fromstring(xml_raw.encode(encoding), parser=parser2)
        return result

    def iews_get_md(self, pid: str, mid: str = None, type_val: str = None, subtype: str = None) -> dict:
        # https://developers.exlibrisgroup.com/rosetta/apis/IEWebServices
        # https://exlibrisgroup.github.io/Rosetta.dps-sdk-projects/current/javadoc/com/exlibris/digitool/repository/ifc/IEWebServices.html#getMD-java.lang.String-java.lang.String-java.lang.String-java.lang.String-java.lang.String-
        client = self.get_client(name='IEWebServices')
        pds_handle = self.get_pds_handle()
        result = {}
        if pds_handle:
            xml_data = client.service.getMD(pds_handle, pid, mid, type_val, subtype)
            result = xml_json(xml_data)
        return result

    def iews_get_dnx(self, pid: str, section: str = None) -> dict:
        # https://developers.exlibrisgroup.com/rosetta/apis/IEWebServices
        # https://exlibrisgroup.github.io/Rosetta.dps-sdk-projects/current/javadoc/com/exlibris/digitool/repository/ifc/IEWebServices.html#getDNX-java.lang.String-java.lang.String-java.lang.String-
        client = self.get_client(name='IEWebServices')
        pds_handle = self.get_pds_handle()
        result = {}
        if pds_handle:
            xml_data = client.service.getDNX(pds_handle, pid, section)
            result = xml_json(xml_data)
        return result

    def ie_retrieve(self, ie_id: str) -> typing.Optional['IEData']:
        ie_data = self.iews_get_ie(ie_id=ie_id, raw=True)
        if ie_data is not None:
            ie = IEData(api=self, xml_data=ie_data)
            return ie
        return None


class RosettaData(object):
    def __init__(self, *args, **kwargs):
        super(RosettaData, self).__init__()
        self._api = kwargs.get('api')  # type: Rosetta
        self._xml_data = kwargs.get('xml_data')  # type: etree.Element
        self._cache_data = {}
        self._pid = None

    @property
    def api(self):
        return self._api

    @property
    def pid(self):
        return self._pid

    @property
    def xml_data(self) -> etree.Element:
        return self._xml_data

    def cache_upsert(self, key, val_fn):
        val = self._cache_data.get('%s.%s' % (self.pid if self.pid else '_', key))
        if not val:
            val = val_fn()
            self._cache_data[key] = val
        return val

    def dmdsec_val(self, pid: str = '', tag_id: str = ''):
        cache_key = '%s.%s.%s' % ('dmdsec_val', pid, tag_id)
        val = self._cache_data.get(cache_key)
        if not val:
            xpath = ''
            if pid:
                xpath += '//mets:dmdSec[@ID="%s-dmd"]' % pid
            if tag_id:
                xpath += '//dc:record//%s' % tag_id
            el = xel(self.xml_data, xpath)
            val = el.text if el is not None else None
            self._cache_data[cache_key] = val
        return val

    def amdsec_val(self, pid: str = '', sec_id: str = '', key_id: str = '', key_text: str = '', key_id_value: str = '',
                   get_section=False):
        cache_key = '%s.%s.%s.%s.%s.%s.%s' % ('amdsec_val', pid, sec_id, key_id, key_text, key_id_value,
                                              str(get_section))
        val = self._cache_data.get(cache_key)
        if not val:
            if key_text:
                key_id = key_id if key_id else 'internalIdentifierType'
                key_id_value = key_id_value if key_id_value else 'internalIdentifierValue'
            xpath = ''
            if pid:
                xpath += '//mets:amdSec[@ID="%s-amd"]' % pid
            if sec_id:
                xpath += '//dnx:section[@id="%s"]' % sec_id
            if key_id:
                xpath += '//dnx:key[@id="%s"]' % key_id
                if key_text:
                    xpath += '[text()="%s"]' % key_text
            if key_id_value:
                xpath += '/../dnx:key[@id="%s"]' % key_id_value
            if get_section:
                xpath += '/../../../../../../..'
            el = xel(self.xml_data, xpath)
            if get_section:
                val = el
            else:
                val = el.text if el is not None else None
            self._cache_data[cache_key] = val
        return val

    def save_xml(self, file_name: str, etree_opts: dict = None):
        etree_opts = etree_opts if isinstance(etree_opts, dict) else {}
        etree_opts = {**{'pretty_print': True, 'xml_declaration': True}, **etree_opts}
        open(file_name, "wb").write(etree.tostring(self.xml_data, **etree_opts))


class IEData(RosettaData):
    def __init__(self, *args, **kwargs):
        super(IEData, self).__init__(*args, **kwargs)
        self._reps = collections.OrderedDict()  # type: typing.Dict[str, 'RepData']
        self._parse()

    @property
    def struct_map_rep_els(self) -> typing.List[etree.Element]:
        els = xels(self._xml_data, './mets:structMap[@TYPE="PHYSICAL"]')
        return els

    @property
    def mid(self):
        return 'ie'

    @property
    def created_by(self):
        return self.cache_upsert('created_by', lambda: self.amdsec_val(self.mid, key_id='createdBy'))

    @property
    def dc_identifier(self):
        return self.cache_upsert('dc_identifier', lambda: self.dmdsec_val(self.mid, tag_id='dc:identifier'))

    @property
    def dc_title(self):
        return self.cache_upsert('dc_title', lambda: self.dmdsec_val(self.mid, tag_id='dc:title'))

    @property
    def dc_source(self):
        return self.cache_upsert('dc_source', lambda: self.dmdsec_val(self.mid, tag_id='dc:source'))

    @property
    def dcterms_isreferencedby(self):
        return self.cache_upsert('dcterms_isreferencedby',
                                 lambda: self.dmdsec_val(self.mid, tag_id='dcterms:isReferencedBy'))

    @property
    def dc_type(self):
        return self.cache_upsert('dc_type', lambda: self.dmdsec_val(self.mid, tag_id='dc:type'))

    @property
    def reps(self) -> typing.Dict[str, 'RepData']:
        return self._reps

    def _parse(self):
        self._pid = self.amdsec_val(self.mid, key_text='PID')
        for rep_el in self.struct_map_rep_els:  # type: dict
            rep = RepData(ie=self, api=self._api, xml_data=self.xml_data, struct_map_el=rep_el)
            self._reps[rep.pid] = rep

    def get_rep(self, rep_code: str, rep_type: str) -> typing.Optional['RepData']:
        for rep_pid, rep in self.reps.items():
            if rep.representation_code == rep_code and rep.preservation_type == rep_type:
                return rep
        return None

    def get_file_pid(self, rep_name: str, file_name: str) -> typing.Optional[str]:
        record = self.amdsec_val(sec_id='generalFileCharacteristics', key_id='fileOriginalPath',
                                 key_text='%s/%s' % (rep_name, file_name), key_id_value='fileOriginalPath',
                                 get_section=True)
        if record is not None:
            file_pid = re.sub(r'-amd$', '', record.get('ID'))
            return file_pid
        return None

    def get_file(self, rep_name: str, file_name: str) -> typing.Optional['FileData']:
        file_pid = self.get_file_pid(rep_name=rep_name, file_name=file_name)
        for rep_pid, rep in self.reps.items():
            fl = rep.files.get(file_pid)
            if fl:
                return fl
        return None


class RepData(RosettaData):
    def __init__(self, *args, **kwargs):
        super(RepData, self).__init__(*args, **kwargs)
        self._ie = kwargs.get('ie')  # type: IEData
        self._struct_map_el = kwargs.get('struct_map_el')  # type: etree.Element
        self._files = collections.OrderedDict()  # type: typing.Dict[str, 'FileData']
        self._mid = None
        self._parse()

    @property
    def ie(self) -> IEData:
        return self._ie

    @property
    def struct_map_el(self) -> etree.Element:
        return self._struct_map_el

    @property
    def mid(self) -> str:
        return self._mid

    @property
    def preservation_type(self) -> str:
        return self.cache_upsert('preservation_type', lambda: self.amdsec_val(self.pid, key_id='preservationType'))

    @property
    def representation_code(self) -> str:
        return self.cache_upsert('representation_code', lambda: self.amdsec_val(self.pid, key_id='RepresentationCode'))

    @property
    def rights_policyid(self) -> str:
        return self.cache_upsert('rights_policyid', lambda: self.amdsec_val(self.pid, key_id='policyId'))

    @property
    def struct_map_file_els(self) -> typing.List[etree.Element]:
        els = xels(self.struct_map_el, './/mets:div[@TYPE="FILE"]')
        return els

    @property
    def files(self) -> typing.Dict[str, 'FileData']:
        return self._files

    def _parse(self):
        self._mid = self.struct_map_el.get('ID')
        self._pid = re.sub(r'-1$', '', self.mid)
        for file_el in self.struct_map_file_els:  # type: etree.Element
            fl = FileData(rep=self, api=self._api, xml_data=self.xml_data, struct_map_el=file_el)
            self._files[fl.pid] = fl


class FileData(RosettaData):
    def __init__(self, *args, **kwargs):
        super(FileData, self).__init__(*args, **kwargs)
        self._rep = kwargs.get('rep')  # type: RepData
        self._struct_map_el = kwargs.get('struct_map_el')  # type: etree.Element
        self._parse()

    @property
    def rep(self) -> RepData:
        return self._rep

    @property
    def struct_map_el(self) -> etree.Element:
        return self._struct_map_el

    @property
    def label(self) -> str:
        return self.cache_upsert('label', lambda: self.struct_map_el.get('LABEL'))

    @property
    def md5(self) -> str:
        return self.cache_upsert('md5', lambda: self.amdsec_val(self.pid, key_id='fixityType',
                                                                key_text='MD5', key_id_value='fixityValue'))

    @property
    def file_original_name(self) -> str:
        return self.cache_upsert('file_original_name', lambda: self.amdsec_val(self.pid, key_id='fileOriginalName'))

    @property
    def dcterms_tableofcontents(self) -> str:
        return self.cache_upsert('dcterms_tableofcontents',
                                 lambda: self.dmdsec_val(self.pid, tag_id='dcterms:tableOfContents'))

    def _parse(self):
        self._pid = xel(self.struct_map_el, './mets:fptr').get('FILEID')
