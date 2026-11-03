const PIPELINE = [
  { step: "01", title: "规格书 spec.yaml", desc: "坐标 + 色板 + 文案 + 元素，双产线唯一事实源" },
  { step: "02", title: "产线① HTML+SVG", desc: "全真实 <text>、独立 id 单元、零位图" },
  { step: "03", title: "产线② 原生 PPTX", desc: "100% 文本框 + 形状，Picture = 0" },
  { step: "04", title: "四道校验门", desc: "文案覆盖 / 无位图 / 边界防溢出 / 截图比对" },
];

const CASES = [
  "德勤AI落地方法论拆解",
  "框架与实施工具",
  "企业AI落地_复刻",
  "AI技术体系对比图",
  "LLM推理全流程_图解",
];

export default function Home() {
  return (
    <main className="page">
      <header className="hero">
        <p className="badge">Snap2Edit Web · v2 预备骨架（PRD F9）</p>
        <h1>
          把静态截图<span className="accent">“复活”</span>为可编辑文件
        </h1>
        <p className="sub">
          一份布局规格（spec.yaml），同步产出全可编辑的 HTML+SVG 与原生 PPTX；
          四道校验门自动把关。当前为 Next.js 基础框架，引擎由 Python CLI（
          <code>src/snap2edit/</code>）提供。
        </p>
        <div className="cta">
          <span className="chip">pip install -e .</span>
          <span className="chip">snap2edit new my-chart</span>
          <span className="chip">snap2edit build &amp;&amp; snap2edit check</span>
        </div>
      </header>

      <section className="grid">
        {PIPELINE.map((p) => (
          <article key={p.step} className="card">
            <span className="step">{p.step}</span>
            <h2>{p.title}</h2>
            <p>{p.desc}</p>
          </article>
        ))}
      </section>

      <section className="cases">
        <h3>已归档案例（docs/）</h3>
        <ul>
          {CASES.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
      </section>

      <footer className="footer">
        MIT © 2026 Snap2Edit Contributors ·{" "}
        <a href="https://github.com/dongf9527/snap2edit">GitHub 仓库</a>
      </footer>
    </main>
  );
}
