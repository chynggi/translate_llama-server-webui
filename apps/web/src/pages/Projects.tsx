import { PageHeader } from "../components/layout/Sidebar";

export function Projects() {
  return (
    <>
      <PageHeader title="Projects" detail="This workspace is reserved for a later milestone." />
      <div className="empty-state">
        <span className="empty-number">2.0</span>
        <h2>Coming in 2.0</h2>
        <p className="muted">
          Project management is outside the MVP. Translation, terminology, and prompt control
          are ready to use now.
        </p>
      </div>
    </>
  );
}
