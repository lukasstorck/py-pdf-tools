# Py PDF Tools

A small collection of tools for pdf files built upon PyMuPDF.
A docker stack runs a web server which provides a front-end for the user to upload files and select the desired tasks.
It also provides an API which handles and processes the requested tasks.
It is also possible to use the tool locally via the command line `python pdf_tools_cli.py -h` or by importing the [core package](./server/src/pdf_tools_core.py).

## Installation and Usage

Clone the repository

```sh
git clone https://github.com/lukasstorck/pdf-tools.git
cd pdf-tools
```

Download, build and run the docker stack

```sh
docker compose up -d
```

Open the browser on <a href="http://localhost:8080" target="_blank">localhost:8080</a> or whatever port you choose in the [docker configuration](./docker-compose.yaml).

## Bookmark Editor

Bookmark editing is currently not included in the server, but can be accessed via the command line interface.

Extract the bookmark (outline) from a pdf file into .json with labels and linked page numbers.
This can then be edited and then recombined into a new pdf file with updated bookmarks (outline).

Example:

```sh
python pdf_tools_cli.py path/to/file/or/folder.pdf -a edit_bookmarks
# edit the .json file
python pdf_tools_cli.py path/to/file/or/folder.pdf -a edit_bookmarks save
```

### Dependencies

- [`FastAPI`](https://github.com/tiangolo/fastapi/tree/master) (MIT License)
- [`PyMuPDF`](https://www.mupdf.com/index.html) (GNU AGPLv3)
- [`python-multipart`](https://github.com/andrew-d/python-multipart) (Apache License 2.0)
- [`Uvicorn`](https://github.com/encode/uvicorn/tree/master) (Modified BSD License)

Install with `pip install fastapi uvicorn PyMuPDF python-multipart` (not needed when used with docker)

### License

This software must be released under the GNU AGPLv3 license due to PyMuPDF's license.
The .gitignore was created with [gitignore.io](https://github.com/toptal/gitignore.io).
The icon .svg was provided by [SVG Repo](https://www.svgrepo.com/svg/38743/pdf).
