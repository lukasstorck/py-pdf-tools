interface Props {
  description: string;
  isSelected: boolean;
  title: string;
  onToggleAction: () => void;
}

function ActionSelection({
  description,
  isSelected,
  title,
  onToggleAction,
}: Props) {
  const color = isSelected ? "text-bg-primary" : "text-bg-secondary";

  return (
    <div className="col">
      <div className={"card h-100 " + color} onClick={onToggleAction}>
        <div className="card-body">
          <h5 className="card-title">{title}</h5>
          <p className="card-text">{description}</p>
        </div>
      </div>
    </div>
  );
}

export default ActionSelection;
