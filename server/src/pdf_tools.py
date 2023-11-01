import argparse
import fitz
import io
import itertools
import json
import logging
import sys
from pathlib import Path

log = logging.getLogger()
log_handler = logging.StreamHandler()
log.addHandler(log_handler)
log_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))


def extract_bookmarks(outline: fitz.Outline):
    """Helper function to extract bookmarks from an pymupdf Outline object."""
    bookmarks = []
    while outline:
        bookmarks.append({
            'label': outline.title,
            'page': outline.page + 1
        })
        if outline.down:
            bookmarks[-1]['subentries'] = extract_bookmarks(outline.down)

        outline = outline.next
    return bookmarks


def convert_bookmarks(bookmarks: list, level=1):
    """Helper function to convert a list of bookmarks to the format expected by pymupdf's `Document.set_toc()`."""
    toc = []
    for bookmark in bookmarks:
        toc.append([level, bookmark['label'], bookmark['page']])
        if 'subentries' in bookmark:
            toc += convert_bookmarks(bookmark['subentries'], level + 1)
    return toc


class Document:
    def __init__(self, file: str = None, stream: bytes | bytearray | io.BytesIO = None, output: str = None):
        # check filetypes and combination
        try:
            self.file = Path(file)
            if not stream and not self.file.is_file():
                raise ValueError('given filename must be a file')

            if self.file.suffix.lower() != '.pdf':
                raise ValueError('given filename must end with ".pdf"')

            if stream:
                if not isinstance(stream, (bytes, bytearray, io.BytesIO)):
                    raise TypeError('stream must be bytes, bytearray or io.BytesIO')

            if stream:
                self.doc = fitz.Document(stream=stream, filename=self.file.name)
            else:
                self.doc = fitz.open(self.file)

            if output:
                self.output_path = Path(output)
                if not self.output_path.is_dir():
                    raise ValueError('output must be a directory or be ommited')
            else:
                self.output_path = self.file.parent

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
            logging.debug(f'No watermarks were found in "{self.file}".')
            return

        for ocg in ocgs:
            variable_type, ocg_settings = self.doc.xref_get_key(ocg, 'Usage')
            ocg_settings = ocg_settings.replace('/ON', '/OFF')
            self.doc.xref_set_key(ocg, 'Usage', ocg_settings)

    def update_permissions(self, value):
        self.permissions = value

    def unlock_permissions(self):
        permissions = fitz.PDF_PERM_PRINT \
            + fitz.PDF_PERM_MODIFY \
            + fitz.PDF_PERM_COPY \
            + fitz.PDF_PERM_ANNOTATE \
            + fitz.PDF_PERM_FORM \
            + fitz.PDF_PERM_ACCESSIBILITY \
            + fitz.PDF_PERM_ASSEMBLE \
            + fitz.PDF_PERM_PRINT_HQ
        # self._update_permissions(-1)
        self.update_permissions(permissions)

    def update_bookmarks(self, new_bookmarks: list[dict]):
        self.doc.set_toc(convert_bookmarks(new_bookmarks))

    def get_bookmarks(self):
        return extract_bookmarks(self.doc.outline)

    def edit_bookmarks(self, bookmark_file=None):
        if not bookmark_file:
            bookmark_file = self.file.with_suffix('.json')

        if bookmark_file.is_file():
            logging.debug(f'updating bookmarks from "{bookmark_file}"')
            with bookmark_file.open() as fp:
                new_bookmarks: list = json.load(fp)
            self.update_bookmarks(new_bookmarks)
        else:
            logging.debug(f'creating bookmark file "{bookmark_file}"')
            bookmarks = self.get_bookmarks()
            with bookmark_file.open('w+') as fp:
                json.dump(bookmarks, fp, indent=4)

    def save(self, overwrite=False):
        if overwrite:
            output_filename = self.file
        else:
            output_filename = self.output_path / (self.file.stem + '_out' + self.file.suffix)
            i = 2
            while output_filename.exists():
                output_filename = self.output_path / (self.file.stem + f'_out{i}' + self.file.suffix)
                i += 1

        logging.debug(f'saving document to "{output_filename}"')
        self.doc.ez_save(output_filename, clean=True,
                         permissions=self.permissions)

    def to_bytes(self):
        return self.doc.tobytes(garbage=3, clean=True, deflate=True,
                                permissions=self.permissions)

    def to_bytesIO(self):
        return io.BytesIO(self.to_bytes())


def _get_documents(path, recursive=False, output=None) -> list[Document]:
    path = Path(path)

    if path.is_file():
        if path.suffix.lower() == '.pdf':
            file = Document(path, output=output)
            return [file]
        else:
            logging.info(f'File "{path}" is not a PDF document.')
    elif path.is_dir():
        if recursive:
            pattern = '**/*.pdf'
        else:
            pattern = '*.pdf'

        documents = []

        if sys.version_info.minor >= 12:
            # "case_sensitive" only in 3.12
            file_path_generator_object = path.glob(pattern, case_sensitive=False)
        else:
            generators = [path.glob(pattern), path.glob(pattern.upper())]
            file_path_generator_object = itertools.chain(*generators)
        for file in file_path_generator_object:
            documents += _get_documents(file, output=output)

        return documents
    else:
        raise logging.warning('"{path}" is neither a file nor a directory.')


def _perform_action(doc: Document, action: str):
    if action.lower() in ['remove_watermarks', 'all']:
        doc.remove_watermarks()
    elif action.lower() in ['unlock_permissions', 'all']:
        doc.unlock_permissions()
    elif action.lower() in ['edit_bookmarks', 'all']:
        doc.edit_bookmarks()
    elif action.lower() in ['save', 'all']:
        doc.save()
    else:
        print(f'Unknown action: {action}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse a path or filename and perform actions.")
    parser.add_argument('file', help='Path or filename to process')
    parser.add_argument('-r', '--recursive', action='store_true', help='Recursively process directory')
    parser.add_argument('-a', '--actions', nargs='*',
                        choices=['remove_watermarks', 'unlock_permissions', 'edit_bookmarks', 'save', 'all'],
                        default=['remove_watermarks', 'unlock_permissions', 'save'],
                        help='List of actions to perform')
    parser.add_argument('-o', '--output', help='Output path for saved files', required=False)
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    documents = _get_documents(args.file, args.recursive, args.output)
    if documents:
        logging.debug('found documents:')
        for document in documents:
            logging.debug(document.file)
        logging.debug('')
    else:
        logging.warning('No documents selected. Exiting now.')
        exit(1)

    if args.actions:
        logging.debug('selected actions:')
        for i, action in enumerate(args.actions):
            logging.debug(f'{i+1}. {action}')
        logging.debug('')
    else:
        logging.warning('No actions specified. Exiting now.')
        exit(1)

    for document in documents:
        logging.debug(f'processing document "{document.file}"')
        for action in args.actions:
            _perform_action(document, action)
        document.doc.close()
