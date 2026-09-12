"""Bounded data inspection and operator-selected resource imports, never extraction."""

import csv
import io
import stat
import zipfile
from pathlib import PurePosixPath

from .common import Fault,digest
from .ingest import SECRET_BYTES,valid_relative
from .local_candidates import fetch_bytes
from .mcp import parse_json
from .storage import no_links


def inspect_resource(raw,format,settings):
    if len(raw)>settings["max_file_bytes"] or SECRET_BYTES.search(raw):
        raise Fault("resource_rejected","Resource size or credential check failed.")
    try:
        if format in {"text","json","csv","tsv"}:
            text=raw.decode("utf-8-sig")
            if format=="json":
                parse_json(text)
            if format in {"csv","tsv"}:
                reader=csv.reader(io.StringIO(text),delimiter="\t" if format=="tsv" else ",")
                width=None
                for index,row in enumerate(reader):
                    if width is None:
                        width=len(row)
                    if not width or len(row)!=width or index>100000:
                        raise ValueError()
            return {"format":format,"text":text[:128000],"preview_truncated":len(text)>128000}
        if format=="zip":
            total,seen,names=0,set(),[]
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                entries=archive.infolist()
                if len(entries)>settings["max_artifacts"]:
                    raise ValueError()
                for item in entries:
                    path=item.filename.rstrip("/")
                    mode=item.external_attr>>16
                    if (not valid_relative(path) or path.casefold() in seen or item.flag_bits&1
                            or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in {0,stat.S_IFREG,stat.S_IFDIR})):
                        raise ValueError()
                    seen.add(path.casefold())
                    total+=item.file_size
                    if item.file_size>settings["max_file_bytes"] or total>settings["max_artifact_bytes"]:
                        raise ValueError()
                    with archive.open(item) as handle:
                        data=handle.read(settings["max_file_bytes"]+1)
                    if len(data)>settings["max_file_bytes"] or SECRET_BYTES.search(data):
                        raise ValueError()
                    names.append({"path":path,"bytes":len(data),"sha256":digest(data)})
            return {"format":"zip","members":names,"extracted":False}
        if format=="binary":
            return {"format":"binary","bytes":len(raw)}
        raise ValueError()
    except (ValueError,UnicodeError,zipfile.BadZipFile,RuntimeError,NotImplementedError,csv.Error,RecursionError):
        raise Fault("resource_invalid","Resource decoding, schema, archive path or expansion limits failed.") from None


def import_configured(settings,name):
    resource=settings["resources"].get(name)
    if resource is None:
        raise Fault("resource_not_authorized","Choose an operator-configured resource name.")
    path=no_links(resource["path"])
    if path.stat().st_size>settings["max_file_bytes"]:
        raise Fault("resource_rejected","Configured resource exceeds its size limit.")
    raw=path.read_bytes()
    if digest(raw)!=resource["sha256"]:
        raise Fault("resource_changed","Configured resource no longer matches its pinned digest.")
    return raw,resource
