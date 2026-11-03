import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Snap2Edit · 截图复刻引擎",
  description:
    "一份布局规格，同步产出全可编辑的 HTML+SVG 与原生 PPTX；四道校验门自动把关。",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
