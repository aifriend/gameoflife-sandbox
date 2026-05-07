// Studio variant of the Life sandbox UI — three-pane IDE layout:
//   left:   pattern library (categorized)
//   center: live canvas + playback controls
//   right:  B/S rule builder, presets, telemetry, population trace
// Aesthetic: retro CRT phosphor — accent #39ff7a, scanlines, vignette, glow.

const { useState, useRef, useEffect, useCallback, useMemo } = React;

// ---------- helpers ----------
function useRaf(active, cb) {
  const cbRef = useRef(cb);
  cbRef.current = cb;
  useEffect(() => {
    if (!active) return;
    let id;
    const tick = (t) => { cbRef.current(t); id = requestAnimationFrame(tick); };
    id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, [active]);
}

// ---------- canvas grid ----------
function LifeCanvas({ board, cell, accent, dim, glow, onPaint, painting, setPainting }) {
  const canvasRef = useRef(null);
  const dpr = window.devicePixelRatio || 1;

  const draw = useCallback(() => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext('2d');
    const w = board.cols * cell;
    const h = board.rows * cell;
    if (c.width !== w * dpr || c.height !== h * dpr) {
      c.width = w * dpr; c.height = h * dpr;
      c.style.width = w + 'px'; c.style.height = h + 'px';
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = dim;
    ctx.fillRect(0, 0, w, h);

    // subtle grid lines (only when cells are big enough to see them)
    if (cell >= 8) {
      ctx.strokeStyle = 'rgba(255,255,255,0.04)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let x = 0; x <= board.cols; x++) {
        ctx.moveTo(x*cell + 0.5, 0); ctx.lineTo(x*cell + 0.5, h);
      }
      for (let y = 0; y <= board.rows; y++) {
        ctx.moveTo(0, y*cell + 0.5); ctx.lineTo(w, y*cell + 0.5);
      }
      ctx.stroke();
    }

    // cells
    if (glow) {
      ctx.shadowColor = accent;
      ctx.shadowBlur = Math.max(4, cell * 0.6);
    } else {
      ctx.shadowBlur = 0;
    }
    ctx.fillStyle = accent;
    const pad = cell >= 8 ? 1 : 0;
    for (let r = 0; r < board.rows; r++) {
      for (let cc = 0; cc < board.cols; cc++) {
        if (board.cells[r * board.cols + cc]) {
          ctx.fillRect(cc * cell + pad, r * cell + pad, cell - pad*2, cell - pad*2);
        }
      }
    }
    ctx.shadowBlur = 0;
  }, [board, cell, accent, dim, glow, dpr]);

  useEffect(() => { draw(); });

  const handlePointer = (e, isDown) => {
    const c = canvasRef.current;
    if (!c) return;
    const rect = c.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const cc = Math.floor(x / cell);
    const r = Math.floor(y / cell);
    if (cc < 0 || cc >= board.cols || r < 0 || r >= board.rows) return;
    onPaint(r, cc, isDown);
  };

  return (
    <canvas
      ref={canvasRef}
      onMouseDown={(e) => { setPainting(true); handlePointer(e, true); }}
      onMouseMove={(e) => { if (painting) handlePointer(e, false); }}
      onMouseUp={() => setPainting(false)}
      onMouseLeave={() => setPainting(false)}
      style={{ display: 'block', cursor: 'crosshair', imageRendering: 'pixelated' }}
    />
  );
}

// ---------- population trace ----------
function PopulationTrace({ data, accent, height = 60, dim }) {
  const ref = useRef(null);
  useEffect(() => {
    const c = ref.current;
    if (!c) return;
    const dpr = window.devicePixelRatio || 1;
    const w = c.clientWidth, h = height;
    c.width = w * dpr; c.height = h * dpr;
    const ctx = c.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = dim;
    ctx.fillRect(0, 0, w, h);
    if (data.length < 2) return;
    const max = Math.max(1, ...data);
    ctx.strokeStyle = accent;
    ctx.lineWidth = 1.25;
    ctx.shadowColor = accent;
    ctx.shadowBlur = 6;
    ctx.beginPath();
    const N = data.length;
    for (let i = 0; i < N; i++) {
      const x = (i / (N - 1)) * w;
      const y = h - (data[i] / max) * (h - 6) - 3;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }, [data, accent, height, dim]);
  return <canvas ref={ref} style={{ width: '100%', height: height + 'px', display: 'block' }} />;
}

// ---------- the main app ----------
function LifeApp({ accent = '#39ff7a', theme = 'phosphor' }) {
  const themes = {
    phosphor: { bg: '#020604', dim: '#04120a', text: '#9ff5b8', muted: '#3d6a4d', border: 'rgba(57,255,122,0.18)' },
    amber:    { bg: '#0a0500', dim: '#180c02', text: '#ffc480', muted: '#7a4f1f', border: 'rgba(255,176,64,0.20)' },
    cyan:     { bg: '#020812', dim: '#04101c', text: '#9fdcff', muted: '#3d6a8f', border: 'rgba(80,200,255,0.20)' },
  };
  const T = themes[theme] || themes.phosphor;

  // Logical grid size is fixed; the cell pixel size adapts to the available
  // space in the center pane so the layout works at any viewport width.
  const ROWS = 60, COLS = 100;
  const canvasFrameRef = useRef(null);
  const [containerSize, setContainerSize] = useState({ w: 900, h: 540 });
  useEffect(() => {
    const el = canvasFrameRef.current;
    if (!el || typeof ResizeObserver === 'undefined') return;
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        const { width, height } = e.contentRect;
        setContainerSize({ w: width, h: height });
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const dims = useMemo(() => {
    // Center pane has 16px padding on each side, plus 6px frame border + 6px padding inside.
    const availW = Math.max(80, containerSize.w - 32 - 24);
    const availH = Math.max(80, containerSize.h - 32 - 24);
    const cell = Math.max(2, Math.min(14, Math.floor(Math.min(availW / COLS, availH / ROWS))));
    return { rows: ROWS, cols: COLS, cell };
  }, [containerSize.w, containerSize.h]);

  const boardRef = useRef(new window.LifeBoard(ROWS, COLS, { rule: 'B3/S23', boundary: 'wrap' }));
  const [, force] = useState(0);
  const rerender = () => force(n => n + 1);

  const [running, setRunning] = useState(false);
  const [speed, setSpeed] = useState(20); // gens/sec
  const [rule, setRule] = useState('B3/S23');
  const [boundary, setBoundary] = useState('wrap');
  const [glow, setGlow] = useState(true);
  const [scanlines, setScanlines] = useState(true);
  const [activePattern, setActivePattern] = useState('gosper_glider_gun');
  const [pop, setPop] = useState([]);
  const [period, setPeriod] = useState(null);
  const [painting, setPainting] = useState(false);
  const lastTickRef = useRef(0);
  const histRef = useRef([]);
  const popRef = useRef([]);

  // load default pattern centered on the board
  useEffect(() => {
    const b = boardRef.current;
    b.clear();
    const pat = window.LIFE_PATTERNS[activePattern];
    const r = Math.floor((b.rows - pat.length) / 2);
    const c = Math.floor((b.cols - pat[0].length) / 2);
    b.placePattern(pat, r, c);
    histRef.current = [];
    popRef.current = [b.population];
    setPop([b.population]);
    setPeriod(null);
    rerender();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePattern]);

  useEffect(() => { boardRef.current.setRule(rule); }, [rule]);
  useEffect(() => { boardRef.current.boundary = boundary; }, [boundary]);

  // FNV-1a hash for cycle/period detection
  const hashBoard = (b) => {
    let h = 2166136261;
    const cells = b.cells;
    for (let i = 0; i < cells.length; i++) {
      h ^= cells[i];
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  };

  useRaf(running, (t) => {
    const b = boardRef.current;
    const interval = 1000 / Math.max(1, speed);
    if (t - lastTickRef.current < interval) return;
    lastTickRef.current = t;
    b.step();
    popRef.current.push(b.population);
    if (popRef.current.length > 240) popRef.current.shift();
    setPop(popRef.current.slice());
    const h = hashBoard(b);
    const idx = histRef.current.findIndex(x => x.h === h);
    if (idx >= 0) {
      setPeriod(histRef.current.length - idx);
    } else {
      histRef.current.push({ h, gen: b.generation });
      if (histRef.current.length > 60) histRef.current.shift();
    }
    rerender();
  });

  const onPaint = (r, c, isDown) => {
    const b = boardRef.current;
    if (isDown) b.toggle(r, c);
    else b.set(r, c, 1);
    rerender();
  };

  const step = () => {
    boardRef.current.step();
    popRef.current.push(boardRef.current.population);
    if (popRef.current.length > 240) popRef.current.shift();
    setPop(popRef.current.slice());
    rerender();
  };
  const clear = () => {
    boardRef.current.clear();
    popRef.current = [0];
    histRef.current = [];
    setPop([0]); setPeriod(null);
    rerender();
  };
  const randomize = (d = 0.3) => {
    boardRef.current.randomize(d);
    popRef.current = [boardRef.current.population];
    histRef.current = [];
    setPop(popRef.current.slice()); setPeriod(null);
    rerender();
  };
  const reload = () => {
    const b = boardRef.current;
    b.clear();
    const pat = window.LIFE_PATTERNS[activePattern];
    const r = Math.floor((b.rows - pat.length) / 2);
    const c = Math.floor((b.cols - pat[0].length) / 2);
    b.placePattern(pat, r, c);
    popRef.current = [b.population]; histRef.current = [];
    setPop(popRef.current.slice()); setPeriod(null);
    rerender();
  };

  const board = boardRef.current;
  const meta = window.PATTERN_META.find(p => p.id === activePattern);
  const baseFont = '"JetBrains Mono", "IBM Plex Mono", ui-monospace, monospace';

  // ---------- subviews ----------
  const Header = () => (
    <div style={{
      display: 'flex', alignItems: 'baseline', gap: 12,
      padding: '10px 16px', borderBottom: `1px solid ${T.border}`, background: T.dim,
    }}>
      <span style={{ color: accent, fontSize: 11, letterSpacing: '0.18em' }}>◉ LIFE.SANDBOX</span>
      <span style={{ color: T.text, fontSize: 13, fontWeight: 600 }}>STUDIO · {meta?.name ?? '—'}</span>
      <span style={{ flex: 1 }} />
      <span style={{ color: T.muted, fontSize: 10 }}>RULE {rule} · {boundary.toUpperCase()} · {board.cols}×{board.rows}</span>
    </div>
  );

  const Btn = ({ children, onClick, primary, hot }) => (
    <button onClick={onClick} style={{
      background: primary ? accent : 'transparent',
      color: primary ? T.bg : (hot ? accent : T.text),
      border: `1px solid ${primary ? accent : T.border}`,
      padding: '6px 12px',
      fontFamily: baseFont,
      fontSize: 11,
      letterSpacing: '0.1em',
      cursor: 'pointer',
      textTransform: 'uppercase',
    }}>{children}</button>
  );

  const PatternList = () => {
    const cats = ['spaceship', 'oscillator', 'still life', 'methuselah', 'gun', 'exotic'];
    return (
      <div style={{ overflow: 'auto', height: '100%', fontSize: 11 }}>
        {cats.map(cat => (
          <div key={cat}>
            <div style={{ padding: '10px 14px 4px', color: T.muted, fontSize: 9, letterSpacing: '0.22em', textTransform: 'uppercase' }}>
              {cat}
            </div>
            {window.PATTERN_META.filter(p => p.cat === cat).map(p => (
              <div key={p.id}
                onClick={() => setActivePattern(p.id)}
                style={{
                  padding: '7px 14px',
                  cursor: 'pointer',
                  borderLeft: `2px solid ${activePattern === p.id ? accent : 'transparent'}`,
                  background: activePattern === p.id ? 'rgba(57,255,122,0.06)' : 'transparent',
                  display: 'flex', justifyContent: 'space-between', gap: 8,
                  color: activePattern === p.id ? accent : T.text,
                }}>
                <span>{p.name}</span>
                <span style={{ color: T.muted, fontSize: 10 }}>{p.note}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  };

  const RuleBuilder = () => {
    const m = /^B([0-8]*)\/S([0-8]*)$/i.exec(rule);
    const birth = new Set((m?.[1] || '').split('').map(Number));
    const survive = new Set((m?.[2] || '').split('').map(Number));
    const toggle = (which, n) => {
      const set = which === 'B' ? new Set(birth) : new Set(survive);
      if (set.has(n)) set.delete(n); else set.add(n);
      const arr = [...set].sort((a,b) => a-b).join('');
      const newRule = which === 'B'
        ? `B${arr}/S${[...survive].sort().join('')}`
        : `B${[...birth].sort().join('')}/S${arr}`;
      setRule(newRule);
    };
    const Row = ({ label, set, which }) => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0' }}>
        <span style={{ width: 18, color: T.muted, fontSize: 10 }}>{label}</span>
        {[0,1,2,3,4,5,6,7,8].map(n => (
          <button key={n} onClick={() => toggle(which, n)} style={{
            width: 22, height: 22, fontFamily: baseFont, fontSize: 10,
            background: set.has(n) ? accent : 'transparent',
            color: set.has(n) ? T.bg : T.muted,
            border: `1px solid ${set.has(n) ? accent : T.border}`,
            cursor: 'pointer',
          }}>{n}</button>
        ))}
      </div>
    );
    return (
      <div style={{ padding: 12 }}>
        <Row label="B" set={birth} which="B" />
        <Row label="S" set={survive} which="S" />
        <div style={{ marginTop: 10, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {window.RULE_PRESETS.map(p => (
            <button key={p.id} onClick={() => setRule(p.id)} style={{
              fontFamily: baseFont, fontSize: 10,
              padding: '4px 8px',
              background: rule === p.id ? 'rgba(57,255,122,0.10)' : 'transparent',
              color: rule === p.id ? accent : T.text,
              border: `1px solid ${rule === p.id ? accent : T.border}`,
              cursor: 'pointer',
            }}>{p.name}</button>
          ))}
        </div>
      </div>
    );
  };

  const Stats = () => {
    const last = pop[pop.length - 1] || 0;
    const peak = Math.max(0, ...pop);
    return (
      <div style={{ padding: 12, fontSize: 11, display: 'grid', gridTemplateColumns: '1fr 1fr', rowGap: 10, columnGap: 10 }}>
        <div><div style={{ color: T.muted, fontSize: 9, letterSpacing: '0.18em' }}>GEN</div><div style={{ color: accent, fontSize: 18 }}>{board.generation.toString().padStart(4,'0')}</div></div>
        <div><div style={{ color: T.muted, fontSize: 9, letterSpacing: '0.18em' }}>POP</div><div style={{ color: accent, fontSize: 18 }}>{last.toString().padStart(4,'0')}</div></div>
        <div><div style={{ color: T.muted, fontSize: 9, letterSpacing: '0.18em' }}>PEAK</div><div style={{ color: T.text, fontSize: 14 }}>{peak}</div></div>
        <div><div style={{ color: T.muted, fontSize: 9, letterSpacing: '0.18em' }}>PERIOD</div><div style={{ color: T.text, fontSize: 14 }}>{period ?? '—'}</div></div>
      </div>
    );
  };

  const Controls = () => (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
      <Btn primary onClick={() => setRunning(r => !r)}>{running ? '❙❙ Pause' : '▶ Run'}</Btn>
      <Btn onClick={step}>Step ›</Btn>
      <Btn onClick={reload}>Reload</Btn>
      <Btn onClick={() => randomize(0.30)}>Soup 30%</Btn>
      <Btn onClick={clear}>Clear</Btn>
      <span style={{ color: T.muted, fontSize: 10, marginLeft: 6 }}>SPEED</span>
      <input type="range" min={1} max={120} value={speed} onChange={(e) => setSpeed(+e.target.value)}
             style={{ accentColor: accent, width: 110 }} />
      <span style={{ color: accent, fontSize: 11, width: 38 }}>{speed}/s</span>
      <span style={{ color: T.muted, fontSize: 10, marginLeft: 6 }}>EDGE</span>
      <Btn hot={boundary==='wrap'} onClick={() => setBoundary(boundary==='wrap'?'fill':'wrap')}>
        {boundary === 'wrap' ? 'Torus' : 'Fixed'}
      </Btn>
      <Btn hot={glow} onClick={() => setGlow(g => !g)}>Glow</Btn>
      <Btn hot={scanlines} onClick={() => setScanlines(s => !s)}>Scan</Btn>
    </div>
  );

  // ---------- layout ----------
  const css = {
    root: {
      background: T.bg, color: T.text, fontFamily: baseFont,
      width: '100%', height: '100%', position: 'relative', overflow: 'hidden',
      letterSpacing: '0.02em',
    },
    scan: scanlines ? {
      position: 'absolute', inset: 0, pointerEvents: 'none',
      background: 'repeating-linear-gradient(180deg, rgba(0,0,0,0) 0px, rgba(0,0,0,0) 2px, rgba(0,0,0,0.20) 3px)',
      mixBlendMode: 'multiply',
    } : null,
    vignette: {
      position: 'absolute', inset: 0, pointerEvents: 'none',
      background: 'radial-gradient(ellipse at center, rgba(0,0,0,0) 55%, rgba(0,0,0,0.55) 100%)',
    },
  };

  return (
    <div style={css.root}>
      <Header />
      <div style={{
        display: 'grid',
        // Sidebars get their preferred width when there's room and shrink down
        // to a sensible minimum on narrow viewports — keeps the 3-pane layout
        // intact at any width without horizontal scrolling.
        gridTemplateColumns: 'minmax(180px, 230px) minmax(0, 1fr) minmax(220px, 280px)',
        gridTemplateRows: '1fr',
        height: 'calc(100% - 41px)',
      }}>
        {/* LEFT — pattern library */}
        <div style={{ borderRight: `1px solid ${T.border}`, minWidth: 0 }}>
          <div style={{ padding: '10px 14px', color: T.muted, fontSize: 10, letterSpacing: '0.18em', borderBottom: `1px solid ${T.border}` }}>PATTERN LIBRARY</div>
          <PatternList />
        </div>

        {/* CENTER — canvas + controls */}
        <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          <div ref={canvasFrameRef} style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16, position: 'relative', minHeight: 0 }}>
            <div style={{ border: `1px solid ${T.border}`, padding: 6, background: T.dim, position: 'relative' }}>
              <LifeCanvas board={board} cell={dims.cell} accent={accent} dim={T.dim} glow={glow}
                onPaint={onPaint} painting={painting} setPainting={setPainting} />
              <div style={{ position: 'absolute', top: 10, left: 14, color: accent, fontSize: 10, letterSpacing: '0.2em', textShadow: glow ? `0 0 6px ${accent}` : 'none' }}>
                GEN {board.generation.toString().padStart(4,'0')}
              </div>
              <div style={{ position: 'absolute', top: 10, right: 14, color: accent, fontSize: 10, letterSpacing: '0.2em' }}>
                POP {board.population.toString().padStart(4,'0')}
              </div>
            </div>
          </div>
          <div style={{ borderTop: `1px solid ${T.border}`, padding: '10px 16px', background: T.dim }}>
            <Controls />
          </div>
        </div>

        {/* RIGHT — rules + telemetry + trace */}
        <div style={{ borderLeft: `1px solid ${T.border}`, display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '10px 14px', color: T.muted, fontSize: 10, letterSpacing: '0.18em', borderBottom: `1px solid ${T.border}` }}>RULE · B/S</div>
          <RuleBuilder />
          <div style={{ padding: '10px 14px', color: T.muted, fontSize: 10, letterSpacing: '0.18em', borderTop: `1px solid ${T.border}`, borderBottom: `1px solid ${T.border}` }}>TELEMETRY</div>
          <Stats />
          <div style={{ padding: '10px 14px', color: T.muted, fontSize: 10, letterSpacing: '0.18em', borderTop: `1px solid ${T.border}` }}>POPULATION TRACE</div>
          <div style={{ padding: 8 }}>
            <PopulationTrace data={pop} accent={accent} dim={T.dim} height={60} />
          </div>
          <div style={{ marginTop: 'auto', padding: '10px 14px', borderTop: `1px solid ${T.border}`, color: T.muted, fontSize: 10, letterSpacing: '0.14em' }}>
            {meta && <>{meta.cat.toUpperCase()} · {meta.size} · {meta.note}</>}
          </div>
        </div>
      </div>
      {scanlines && <div style={css.scan} />}
      <div style={css.vignette} />
    </div>
  );
}

window.LifeApp = LifeApp;
