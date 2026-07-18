import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/layout/Sidebar";
import { Chat } from "./pages/Chat";
import { Glossary } from "./pages/Glossary";
import { Logs } from "./pages/Logs";
import { Presets } from "./pages/Presets";
import { Projects } from "./pages/Projects";
import { PromptPreview } from "./pages/PromptPreview";
import { Settings } from "./pages/Settings";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Chat />} />
        <Route path="/projects" element={<Projects />} />
        <Route path="/glossary" element={<Glossary />} />
        <Route path="/presets" element={<Presets />} />
        <Route path="/prompt" element={<PromptPreview />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}
