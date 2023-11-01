import fitz
import io
import logging

from pathlib import Path

log = logging.getLogger()
log_handler = logging.StreamHandler()
log.addHandler(log_handler)
log_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))


def set_log_level(level: int | str):
    log.setLevel(level)


ALL_PERMISSIONS_GRANTED = fitz.PDF_PERM_PRINT \
    + fitz.PDF_PERM_MODIFY \
    + fitz.PDF_PERM_COPY \
    + fitz.PDF_PERM_ANNOTATE \
    + fitz.PDF_PERM_FORM \
    + fitz.PDF_PERM_ACCESSIBILITY \
    + fitz.PDF_PERM_ASSEMBLE \
    + fitz.PDF_PERM_PRINT_HQ


def _extract_bookmarks(outline: fitz.Outline):
    """Helper function to extract bookmarks from an pymupdf Outline object."""
    bookmarks = []
    while outline:
        bookmarks.append({
            'label': outline.title,
            'page': outline.page + 1
        })
        if outline.down:
            bookmarks[-1]['subentries'] = _extract_bookmarks(outline.down)

        outline = outline.next
    return bookmarks


def _convert_bookmarks(bookmarks: list, level=1):
    """Helper function to convert a list of bookmarks to the format expected by pymupdf's `Document.set_toc()`."""
    toc = []
    for bookmark in bookmarks:
        toc.append([level, bookmark['label'], bookmark['page']])
        if 'subentries' in bookmark:
            toc += _convert_bookmarks(bookmark['subentries'], level + 1)
    return toc


class Document:
    def __init__(self, filename: str, data: bytes | bytearray | io.BytesIO):
        self.file = Path(filename)
        try:
            if self.file.suffix.lower() != '.pdf':
                raise ValueError('given filename must end with ".pdf"')

            if not isinstance(data, (bytes, bytearray, io.BytesIO)):
                raise TypeError('stream must be bytes, bytearray or io.BytesIO')

            self.doc = fitz.Document(stream=data, filename=self.file.name)
            self.permissions = self.doc.permissions
        except Exception as e:
            logging.error(f'Failed to create document: {e}')

    def remove_watermarks(self):
        ocgs = set()
        try:
            for key in ['on', 'off']:
                if key in self.doc.get_layer(-1):
                    ocgs.update(self.doc.get_layer(-1)[key])
        except BaseException:
            pass

        if not ocgs:
            logging.debug(f'No watermarks were found in "{str(self.file)}".')
            return

        for ocg in ocgs:
            variable_type, ocg_settings = self.doc.xref_get_key(ocg, 'Usage')
            ocg_settings = ocg_settings.replace('/ON', '/OFF')
            self.doc.xref_set_key(ocg, 'Usage', ocg_settings)

    def update_permissions(self, value):
        self.permissions = value

    def unlock_permissions(self):
        # self._update_permissions(-1)
        self.update_permissions(ALL_PERMISSIONS_GRANTED)

    def update_bookmarks(self, new_bookmarks: list[dict]):
        self.doc.set_toc(_convert_bookmarks(new_bookmarks))

    def get_bookmarks(self):
        return _extract_bookmarks(self.doc.outline)

    def to_bytes(self):
        return self.doc.tobytes(garbage=3, clean=True, deflate=True,
                                permissions=self.permissions)

    def to_bytesIO(self):
        return io.BytesIO(self.to_bytes())
