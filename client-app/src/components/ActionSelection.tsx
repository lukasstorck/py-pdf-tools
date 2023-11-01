import ActionCard from "./ActionCard";
import { Action } from "./types";

interface Props {
  availableActions: Action[];
  onToggleAction: (action: Action) => void;
  selectedActions: Action[];
  uploadInProgress: boolean;
  onUpload: () => void;
}

function ActionSelection({
  availableActions,
  onToggleAction,
  selectedActions,
  uploadInProgress,
  onUpload,
}: Props) {
  return (
    <div className="container mt-4">
      <div className="row row-cols-1 row-cols-md-4 g-4">
        {availableActions.map((action) => (
          <ActionCard
            key={action.id}
            title={action.title}
            description={action.description}
            onToggleAction={() => onToggleAction(action)}
            isSelected={selectedActions.includes(action)}
          />
        ))}
      </div>
      <div className="container mt-4 mb-4">
        <div className="row">
          <div className="col-md-8">
            <h4>Selected Actions:</h4>
            <ul>
              {selectedActions.length === 0 && (
                <li className="text-muted">none</li>
              )}
              {selectedActions.map((action) => (
                <li key={action.id}>{action.title}</li>
              ))}
            </ul>
          </div>

          <div className="col-md-4 d-flex align-items-center justify-content-center">
            <button
              className="btn btn-primary btn-lg pt-4 pb-4 w-100 d-flex align-items-center justify-content-around"
              disabled={selectedActions.length === 0}
              onClick={onUpload}
            >
              <span>Upload and Process</span>
              {uploadInProgress && <span className="spinner-border"></span>}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ActionSelection;
