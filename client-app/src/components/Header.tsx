import { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

function Header({ children }: Props) {
  return (
    <header>
      <div className="m-4">
        <h1 className="text-center">{children}</h1>
      </div>
    </header>
  );
}

export default Header;
