import { useState, useEffect, SyntheticEvent } from "react";
import Dropzone from "./components/Dropzone";
import Header from "./components/Header";
import ActionSelection from "./components/ActionSelection";
import { Action } from "./components/types";

function App() {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedActions, setSelectedActions] = useState<Action[]>([]);
  const [availableActions, setAvailableActions] = useState<Action[]>([]);
  const [uploadInProgress, setUploadInProgress] = useState(false);

  useEffect(() => {
    const fetchAvailableActions = async () => {
      try {
        const response = await fetch("/api/get-available-actions");
        if (response.ok) {
          const data = await response.json();
          setAvailableActions(data);
        } else {
          console.error("Failed to fetch available actions");
        }
      } catch (error) {
        console.error("Error fetching available actions:", error);
      }
    };

    fetchAvailableActions();
  }, []);

  const handleDrop = (files: File[]) => {
    setSelectedFiles((prevUploadedFiles) => {
      const uniqueFiles = files.filter(
        (file) =>
          !prevUploadedFiles.some((prevFile) => prevFile.name === file.name)
      );
      return [...prevUploadedFiles, ...uniqueFiles];
    });
  };

  const handleRemoveFile = (file: File, event: SyntheticEvent) => {
    event.stopPropagation();
    setSelectedFiles((prevUploadedFiles) =>
      prevUploadedFiles.filter((item) => item !== file)
    );
  };

  const handleToggleAction = (action: Action) => {
    if (selectedActions.includes(action)) {
      setSelectedActions((prevSelectedActions) =>
        prevSelectedActions.filter((item) => item != action)
      );
    } else {
      setSelectedActions((prevSelectedActions) => [
        ...prevSelectedActions,
        action,
      ]);
    }
  };

  const handleUpload = async () => {
    if (selectedActions.length === 0 || selectedFiles.length === 0) return;

    setUploadInProgress(true);

    try {
      const formData = new FormData();
      selectedActions.forEach((action) => {
        formData.append("actions", action.id);
      });
      selectedFiles.forEach((file) => {
        formData.append("files", file);
      });

      const response = await fetch("/api/process-files", {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        const blob = await response.blob();
        const contentDispositionHeader = response.headers.get(
          "Content-Disposition"
        );

        let filename = "processed_file";
        if (contentDispositionHeader) {
          const filenameMatch = contentDispositionHeader.match(/filename=(.+)/);
          if (filenameMatch) filename = filenameMatch[1];
        }

        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.style.display = "none";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
      } else {
        console.error("Failed to upload and fetch processed files.");
      }
    } catch (error) {
      console.error("Error uploading and fetching processed files:", error);
    }

    setUploadInProgress(false);
  };

  return (
    <>
      <Header>PDF tools</Header>
      <Dropzone
        onDrop={handleDrop}
        uploadedFiles={selectedFiles}
        onRemoveFile={handleRemoveFile}
      />
      {selectedFiles.length !== 0 && (
        <ActionSelection
          availableActions={availableActions}
          onToggleAction={handleToggleAction}
          selectedActions={selectedActions}
          uploadInProgress={uploadInProgress}
          onUpload={handleUpload}
        />
      )}
    </>
  );
}

export default App;
