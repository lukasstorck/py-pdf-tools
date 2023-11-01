# PDF Tools

A small collection of tools for pdf files built upon FastAPI and PyMuPDF with Docker.

## TODO:

- extract Document into pdf_tools_core.py and only in-memory
- write pdf_tools_cli.py for the rest

## Bookmark Editor

Bookmark editing is currently not included in the server, but can be accessed via the command line interface.

Extract the bookmark (outline) from a pdf file into .json with labels and linked page numbers.
This can then be edited and then recombined into a new pdf file with updated bookmarks (outline).

Example:

```bash
python server/src/pdf_tools.py path/to/pdf/file/or/folder.pdf -a edit_bookmarks
# edit the .json file
python server/src/pdf_tools.py path/to/pdf/file/or/folder.pdf -a edit_bookmarks save
```

### Dependencies

- `PyMuPDF`
- `FastAPI`
- `Uvicorn`
- `python-multipart`

Install with `pip install fastapi uvicorn PyMuPDF python-multipart` (not needed when used with docker)

### License

This software must be released under the AGPLv3 license due to PyMuPDF's license.
