import { ReactNode } from "react";

interface Props {
  children: ReactNode;
}

function Header({ children }: Props) {
  return (
    <header>
      <div className="m-4 d-flex justify-content-center align-items-center flex-wrap">
        <h1 className="text-center inline m-0">{children}</h1>
        <div className="text-center mx-3">
          <a
            href="https://github.com/lukasstorck/py-pdf-tools"
            target="_blank"
            className="text-muted text-decoration-none text-no-warp"
          >
            <span>view source</span>
            <img
              src="github-mark.svg"
              alt="Github Logo"
              style={{ height: "1rem" }}
              className="mx-1"
            />
          </a>
        </div>
      </div>
    </header>
  );
}

export default Header;
