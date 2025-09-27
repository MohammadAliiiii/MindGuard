<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Human Risk Management App — README</title>

  <!-- Minimal, GitHub-friendly styles. Keeps everything inline so the file is self-contained. -->
  <style>
    :root{
      --bg:#0f1724; --card:#0b1220; --muted:#9aa7bf; --accent:#60a5fa; --glass: rgba(255,255,255,0.03);
      --radius:12px; font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial;
    }
    html,body{height:100%;margin:0;background:linear-gradient(180deg,var(--bg),#071028);color:#e6eef8;}
    .wrap{max-width:980px;margin:40px auto;padding:28px;background:linear-gradient(180deg,rgba(255,255,255,0.02), rgba(255,255,255,0.01));box-shadow:0 8px 30px rgba(2,6,23,0.7);border-radius:18px;border:1px solid rgba(255,255,255,0.03)}
    header{display:flex;align-items:center;gap:16px}
    .logo{
      width:64px;height:64px;border-radius:14px;background:linear-gradient(135deg,var(--accent),#7dd3fc);display:flex;align-items:center;justify-content:center;color:#05203b;font-weight:700;font-size:20px;box-shadow:0 6px 18px rgba(96,165,250,0.12)
    }
    h1{margin:0;font-size:22px;letter-spacing:0.2px}
    p.lead{margin:6px 0 18px;color:var(--muted);font-size:14px}
    .meta{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}
    .pill{background:var(--glass);padding:8px 12px;border-radius:999px;font-size:13px;color:var(--muted);border:1px solid rgba(255,255,255,0.02)}
    section{margin-top:18px}
    h2{font-size:16px;margin:8px 0 10px}
    ul{margin:8px 0 18px;padding-left:20px;color:var(--muted)}
    code, pre{background:rgba(0,0,0,0.2);padding:8px;border-radius:8px;font-family:ui-monospace, SFMono-Regular, Menlo, Monaco, "Roboto Mono", "Courier New", monospace;color:#dff1ff}
    pre{overflow:auto}
    .grid{display:grid;grid-template-columns:1fr 300px;gap:18px}
    @media (max-width:880px){.grid{grid-template-columns:1fr}}
    .card{background:linear-gradient(180deg,rgba(255,255,255,0.015),rgba(255,255,255,0.01));padding:14px;border-radius:12px;border:1px solid rgba(255,255,255,0.02)}
    footer{margin-top:20px;color:var(--muted);font-size:13px;text-align:center}
    a.inline{color:var(--accent);text-decoration:none}
  </style>
</head>
<body>
  <main class="wrap" role="main" aria-labelledby="title">
    <header>
      <div class="logo">HR</div>
      <div>
        <h1 id="title">Human Risk Management App</h1>
        <p class="lead">Lightweight Python nudges for safer behavior — little reminders that make security a habit.</p>
        <div class="meta" aria-hidden="true">
          <span class="pill">Python</span>
          <span class="pill">Security Awareness</span>
          <span class="pill">Habit-forming Nudges</span>
          <span class="pill">MIT License</span>
        </div>
      </div>
    </header>

    <div class="grid" role="region" aria-label="main content">
      <div>
        <section class="card" id="features">
          <h2>Features</h2>
          <ul>
            <li>🛡️ Timely security nudges (e.g., “Always lock your computer before stepping away”).</li>
            <li>⏲️ Idle reminders when a user is inactive for configurable intervals.</li>
            <li>⚙️ Customizable messages via <code>messages.txt</code> and settings in <code>config.yaml</code>.</li>
            <li>🧪 Test suite included to make changes safe and reviewable.</li>
          </ul>
        </section>

        <section class="card" id="install">
          <h2>Installation</h2>
          <p class="muted" style="color:var(--muted)">Grab the repo, create a virtual environment, and install dependencies.</p>
          <pre><code># clone
git clone https://github.com/your-username/human-risk-management-app.git
cd human-risk-management-app

# create venv and install
python3 -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
pip install -r requirements.txt
</code></pre>
        </section>

        <section class="card" id="usage">
          <h2>Usage</h2>
          <p>Run the app from the repository root. The command below assumes your package entry is set up in <code>setup.py</code> or a module runner exists in <code>src/</code>.</p>
          <pre><code>python -m src
# or, if installed as a package:
python setup.py install
human-risk-app
</code></pre>
          <p style="color:var(--muted)">Edit <code>messages.txt</code> and <code>config.yaml</code> to change prompts and timing.</p>
        </section>

        <section class="card" id="development">
          <h2>Development</h2>
          <ul>
            <li>Install dev dependencies: <code>pip install -r requirements-dev.txt</code></li>
            <li>Run tests: <code>pytest tests/</code></li>
            <li>Use <code>Makefile</code> targets for common tasks (build, lint, test).</li>
          </ul>
        </section>

        <section class="card" id="structure">
          <h2>Project Structure</h2>
          <pre><code>src/              # Main application code
tests/            # Unit tests
scripts/          # Helper scripts
deployment/       # Deployment configs (no secrets)
config.yaml       # App configuration (do not commit secrets)
messages.txt      # Security awareness messages
README.md         # This README
</code></pre>
        </section>
      </div>

      <aside>
        <section class="card" id="quick-tip">
          <h2>80/20 Tip (what matters)</h2>
          <p style="color:var(--muted)">Upload the 20% of files that give others 80% of value: <strong>source, tests, requirements, README, config (no secrets), and build scripts</strong>. Add a <code>.gitignore</code> to keep builds and logs out.</p>
        </section>

        <section class="card" id="gitignore-sample">
          <h2>Suggested <code>.gitignore</code></h2>
          <pre><code># Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd

# Virtual envs
venv/
build_env/

# Build & packaging
build/
dist/
*.egg-info/

# Logs
*.log

# Editor files
.vscode/
.idea/
*.swp
</code></pre>
        </section>

        <section class="card" id="contribute">
          <h2>Contributing</h2>
          <p style="color:var(--muted)">Pull requests welcome. Open an issue first for major changes and include tests for new behavior.</p>
        </section>
      </aside>
    </div>

    <footer>
      <p>Made with a slightly nerdy grin — keep people safe, one friendly nudge at a time. • <a class="inline" href="LICENSE">MIT License</a></p>
    </footer>
  </main>
</body>
</html>

pytest tests/
```
