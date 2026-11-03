import type { Metadata } from "next";
import StudioEditor from "./editor";

export const metadata: Metadata = {
  title: "可视化编辑器 · Snap2Edit",
  description: "spec.yaml 在线可视化编辑：点选、拖拽、改属性，YAML 实时同步，一键构建预览双产物",
};

export default function StudioPage() {
  return (
    <main className="page">
      <StudioEditor />
      <footer className="footer">
        MIT © 2026 Snap2Edit Contributors ·{" "}
        <a href="https://github.com/dongf9527/snap2edit">GitHub 仓库</a>
      </footer>
    </main>
  );
}
