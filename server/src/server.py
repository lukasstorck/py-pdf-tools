import datetime
import io
import os
import pathlib
import uvicorn
import zipfile

from fastapi import FastAPI, HTTPException, status, UploadFile
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from traceback import format_exc


from src.pdf_tools_core import Document

app = FastAPI(title='webpage-app')
api_app = FastAPI(title='api-app')

website_path = pathlib.Path('src/website.html')
logs_path = pathlib.Path('logs/')


def log_error(event, message):
    if not logs_path.is_dir():
        os.makedirs(logs_path)

    log_file_path = logs_path / f'{str(datetime.datetime.now())}.log'
    with log_file_path.open('w+') as fp:
        fp.write(f'Error Message: {message}\nError: {format_exc()}\n')
    raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message)


available_actions = [
    {
        'id': 'remove_watermarks',
        'title': 'Remove Watermarks',
        'description': 'Remove watermarks by disabeling Optional Content Groups (OCG) within the PDF.'
    },
    {
        'id': 'unlock_permissions',
        'title': 'Unlock Permissions',
        'description': 'Unlock all permissions in the PDF (given that it is not encrypted). This includes making the PDF editable for note taking.'
    }
]

app.mount('/api', api_app)
app.mount('/', StaticFiles(directory='client', html=True), name='client')


@api_app.post('/process-files')
async def process_files(files: list[UploadFile], actions: list[str]):
    try:
        processed_files: list[Document] = []
        for file in files:
            content = await file.read()
            doc = Document(filename=file.filename, data=content)
            for action in actions:
                if action == 'remove_watermarks':
                    doc.remove_watermarks()
                elif action == 'unlock_permissions':
                    doc.unlock_permissions()
            processed_files.append(doc)

        if len(processed_files) == 1:
            doc = processed_files[0]
            output_file_name = doc.file
            output_file_content = doc.to_bytesIO()
            content_type = 'application/pdf'
        else:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for doc in processed_files:
                    zipf.writestr(doc.file, doc.to_bytes())
            zip_buffer.seek(0)

            output_file_name = 'processed_files.zip'
            output_file_content = zip_buffer
            content_type = 'application/zip'

        return StreamingResponse(output_file_content, headers={
            'Content-Disposition': f'attachment; filename={output_file_name}',
            'Content-Type': content_type
        })
    except Exception as e:
        log_error(e, 'Encountered an error during processing.')


@api_app.get('/get-available-actions')
async def get_available_actions():
    try:
        return available_actions
    except Exception as e:
        log_error(e, 'Encountered an error during processing.')


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8080)
