import argparse
import itertools
import json
import logging
import sys

from pathlib import Path

from server.src.pdf_tools_core import Document, set_log_level

log = logging.getLogger()
log_handler = logging.StreamHandler()
log.addHandler(log_handler)
log_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

output_path = None


def _get_documents(path, recursive=False) -> list[Document]:
    path = Path(path)
    if path.is_file():
        if path.suffix.lower() == '.pdf':
            with path.open('rb') as fp:
                file = Document(filename=path, data=fp.read())
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
            documents += _get_documents(file)

        return documents
    else:
        raise logging.warning(f'"{path}" is neither a file nor a directory.')


def _perform_action(doc: Document, action: str):
    if action.lower() in ['remove_watermarks']:
        doc.remove_watermarks()
    elif action.lower() in ['unlock_permissions']:
        doc.unlock_permissions()
    elif action.lower() in ['edit_bookmarks']:
        bookmark_file = doc.file.with_suffix('.json')

        if bookmark_file.is_file():
            logging.debug(f'updating bookmarks from "{bookmark_file}"')
            with bookmark_file.open() as fp:
                new_bookmarks: list = json.load(fp)
            doc.update_bookmarks(new_bookmarks)
        else:
            logging.debug(f'creating bookmark file "{bookmark_file}"')
            bookmarks = doc.get_bookmarks()
            with bookmark_file.open('w+') as fp:
                json.dump(bookmarks, fp, indent=4)
    elif action.lower() in ['save']:
        if not output_path:
            output_path = doc.file.parent
        output_filename = output_path / (doc.file.stem + '_out' + doc.file.suffix)

        i = 2
        while output_filename.exists():
            output_filename = output_path / (doc.file.stem + f'_out{i}' + doc.file.suffix)
            i += 1

        logging.debug(f'saving document to "{output_filename}"')
        with open(output_filename, 'wb') as fp:
            fp.write(doc.to_bytes())
    else:
        logging.warning(f'ignoring unknown action: {action}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Parse a path or filename and perform actions.")
    parser.add_argument('file', help='Path or filename to process')
    parser.add_argument('-r', '--recursive', action='store_true', help='Recursively process directory')
    parser.add_argument('-a', '--actions', nargs='*',
                        choices=['remove_watermarks', 'unlock_permissions', 'edit_bookmarks', 'save'],
                        default=['remove_watermarks', 'unlock_permissions', 'save'],
                        help='List of actions to perform')
    parser.add_argument('-o', '--output', help='Output path for saved files', required=False)
    parser.add_argument('-v', '--verbose', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)
        set_log_level(logging.DEBUG)

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_dir():
            logging.warning('If specified, output path must be a valid directory. Exiting now.')
            exit(1)

    documents = _get_documents(args.file, args.recursive)
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
