import { SyntheticEvent } from "react";
import { useDropzone } from "react-dropzone";
import styled from "styled-components";

const Container = styled.div`
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  border-width: 2px;
  border-radius: 2px;
  border-color: #eeeeee;
  border-style: dashed;
  background-color: #fafafa;
  color: #bdbdbd;
  outline: none;
  transition: border 0.24s ease-in-out;
`;

interface Props {
  onDrop: (files: File[]) => void;
  uploadedFiles: File[];
  onRemoveFile: (file: File, event: SyntheticEvent) => void;
}

function Dropzone({ onDrop, uploadedFiles, onRemoveFile }: Props) {
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
  });

  const text = isDragActive
    ? "Drop the files here ..."
    : "Drag 'n' drop some files here, or click to select files";

  return (
    <div className="container">
      <Container {...getRootProps()}>
        <input {...getInputProps()} />
        {uploadedFiles.length === 0 ? (
          <div className="container text-center">
            <p> {text}</p>
            <small className="text-muted">
              By using this online tool, you consent to the upload of the
              selected files to a server where the files are processed.
            </small>
          </div>
        ) : (
          <div className="container">
            <ul className="list-group">
              {uploadedFiles.map((file) => (
                <li
                  key={file.name}
                  className="list-group-item d-flex justify-content-between"
                >
                  <span>{file.name}</span>
                  <button
                    type="button"
                    onClick={(event) => onRemoveFile(file, event)}
                    className="btn btn-sm btn-outline-danger"
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </Container>
    </div>
  );
}

export default Dropzone;
