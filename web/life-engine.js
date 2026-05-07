// Conway's Game of Life engine — rule-agnostic B/S notation.
// Pure JS, no deps. Toroidal (wrap) or fill boundary.
// Patterns are kept in sync with the Python project's bundled .rle files.

(function () {
  function parseRule(rule) {
    // "B3/S23" -> { birth: Set([3]), survive: Set([2,3]) }
    const m = /^B([0-8]*)\/S([0-8]*)$/i.exec(rule.trim());
    if (!m) return { birth: new Set([3]), survive: new Set([2, 3]) };
    return {
      birth: new Set(m[1].split('').map(Number)),
      survive: new Set(m[2].split('').map(Number)),
    };
  }

  class LifeBoard {
    constructor(rows, cols, opts = {}) {
      this.rows = rows;
      this.cols = cols;
      this.boundary = opts.boundary || 'wrap'; // 'wrap' or 'fill'
      this.rule = opts.rule || 'B3/S23';
      this._rule = parseRule(this.rule);
      this.cells = new Uint8Array(rows * cols);
      this._next = new Uint8Array(rows * cols);
      this.generation = 0;
      this.population = 0;
    }
    setRule(rule) {
      this.rule = rule;
      this._rule = parseRule(rule);
    }
    idx(r, c) { return r * this.cols + c; }
    get(r, c) { return this.cells[r * this.cols + c]; }
    set(r, c, v) {
      const i = r * this.cols + c;
      const old = this.cells[i];
      const nv = v ? 1 : 0;
      if (old !== nv) {
        this.cells[i] = nv;
        this.population += nv - old;
      }
    }
    toggle(r, c) { this.set(r, c, 1 - this.cells[this.idx(r, c)]); }
    clear() {
      this.cells.fill(0);
      this.generation = 0;
      this.population = 0;
    }
    randomize(density = 0.3) {
      let pop = 0;
      for (let i = 0; i < this.cells.length; i++) {
        const v = Math.random() < density ? 1 : 0;
        this.cells[i] = v;
        pop += v;
      }
      this.population = pop;
      this.generation = 0;
    }
    placePattern(pattern, rOff, cOff) {
      const h = pattern.length;
      const w = pattern[0].length;
      for (let r = 0; r < h; r++) {
        for (let c = 0; c < w; c++) {
          const rr = rOff + r;
          const cc = cOff + c;
          if (rr >= 0 && rr < this.rows && cc >= 0 && cc < this.cols) {
            this.set(rr, cc, pattern[r][c]);
          }
        }
      }
    }
    step() {
      const { rows, cols, cells, _next, _rule, boundary } = this;
      let pop = 0;
      const wrap = boundary === 'wrap';
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          let n = 0;
          for (let dr = -1; dr <= 1; dr++) {
            for (let dc = -1; dc <= 1; dc++) {
              if (dr === 0 && dc === 0) continue;
              let rr = r + dr, cc = c + dc;
              if (wrap) {
                if (rr < 0) rr += rows; else if (rr >= rows) rr -= rows;
                if (cc < 0) cc += cols; else if (cc >= cols) cc -= cols;
              } else {
                if (rr < 0 || rr >= rows || cc < 0 || cc >= cols) continue;
              }
              n += cells[rr * cols + cc];
            }
          }
          const alive = cells[r * cols + c];
          let nv = 0;
          if (alive) nv = _rule.survive.has(n) ? 1 : 0;
          else nv = _rule.birth.has(n) ? 1 : 0;
          _next[r * cols + c] = nv;
          pop += nv;
        }
      }
      const tmp = this.cells;
      this.cells = this._next;
      this._next = tmp;
      this.population = pop;
      this.generation++;
    }
  }

  // -------------------------------------------------------------- patterns
  // Each pattern is a 2D array of 0/1 — exact same canonical phases as the
  // .rle files in the Python project's patterns/ directory.

  function fromAscii(rows) {
    return rows.map(row => [...row].map(ch => ch === 'O' ? 1 : 0));
  }

  const P = {
    // spaceships
    glider: [
      [0,1,0],
      [0,0,1],
      [1,1,1],
    ],
    lwss: [
      [0,1,1,1,1],
      [1,0,0,0,1],
      [0,0,0,0,1],
      [1,0,0,1,0],
    ],
    mwss: [
      [0,0,1,0,0,0],
      [1,0,0,0,1,0],
      [0,0,0,0,0,1],
      [1,0,0,0,0,1],
      [0,1,1,1,1,1],
    ],
    hwss: [
      [0,0,1,1,0,0,0],
      [1,0,0,0,0,1,0],
      [0,0,0,0,0,0,1],
      [1,0,0,0,0,0,1],
      [0,1,1,1,1,1,1],
    ],

    // oscillators
    blinker: [[1,1,1]],
    toad: [
      [0,1,1,1],
      [1,1,1,0],
    ],
    beacon: [
      [1,1,0,0],
      [1,1,0,0],
      [0,0,1,1],
      [0,0,1,1],
    ],
    pulsar: fromAscii([
      '..OOO...OOO..',
      '.............',
      'O....O.O....O',
      'O....O.O....O',
      'O....O.O....O',
      '..OOO...OOO..',
      '.............',
      '..OOO...OOO..',
      'O....O.O....O',
      'O....O.O....O',
      'O....O.O....O',
      '.............',
      '..OOO...OOO..',
    ]),
    pentadecathlon: fromAscii([
      '..O....O..',
      'OO.OOOO.OO',
      '..O....O..',
    ]),

    // still lifes
    block: [[1,1],[1,1]],
    beehive: [
      [0,1,1,0],
      [1,0,0,1],
      [0,1,1,0],
    ],
    loaf: [
      [0,1,1,0],
      [1,0,0,1],
      [0,1,0,1],
      [0,0,1,0],
    ],
    boat: [
      [1,1,0],
      [1,0,1],
      [0,1,0],
    ],
    tub: [
      [0,1,0],
      [1,0,1],
      [0,1,0],
    ],

    // methuselahs
    r_pentomino: [
      [0,1,1],
      [1,1,0],
      [0,1,0],
    ],
    acorn: [
      [0,1,0,0,0,0,0],
      [0,0,0,1,0,0,0],
      [1,1,0,0,1,1,1],
    ],
    diehard: [
      [0,0,0,0,0,0,1,0],
      [1,1,0,0,0,0,0,0],
      [0,1,0,0,0,1,1,1],
    ],
    bunnies: [
      [1,0,0,0,0,0,0,1],
      [0,0,1,0,0,0,1,0],
      [0,0,1,0,0,1,0,1],
      [0,1,0,1,0,0,0,0],
    ],

    // guns
    gosper_glider_gun: fromAscii([
      '........................O...........',
      '......................O.O...........',
      '............OO......OO............OO',
      '...........O...O....OO............OO',
      'OO........O.....O...OO..............',
      'OO........O...O.OO....O.O...........',
      '..........O.....O.......O...........',
      '...........O...O....................',
      '............OO......................',
    ]),

    // exotic
    eater: [
      [1,1,0,0],
      [1,0,1,0],
      [0,0,1,0],
      [0,0,1,1],
    ],
  };

  const PATTERN_META = [
    { id: 'glider',             name: 'Glider',             cat: 'spaceship',    size: '3×3',   period: 4,    note: 'c/4 diagonal' },
    { id: 'lwss',               name: 'LWSS',               cat: 'spaceship',    size: '5×4',   period: 4,    note: 'lightweight' },
    { id: 'mwss',               name: 'MWSS',               cat: 'spaceship',    size: '6×5',   period: 4,    note: 'middleweight' },
    { id: 'hwss',               name: 'HWSS',               cat: 'spaceship',    size: '7×5',   period: 4,    note: 'heavyweight' },
    { id: 'blinker',            name: 'Blinker',            cat: 'oscillator',   size: '3×1',   period: 2,    note: 'p2' },
    { id: 'toad',               name: 'Toad',               cat: 'oscillator',   size: '4×2',   period: 2,    note: 'p2' },
    { id: 'beacon',             name: 'Beacon',             cat: 'oscillator',   size: '4×4',   period: 2,    note: 'p2' },
    { id: 'pulsar',             name: 'Pulsar',             cat: 'oscillator',   size: '13×13', period: 3,    note: 'p3' },
    { id: 'pentadecathlon',     name: 'Pentadecathlon',     cat: 'oscillator',   size: '10×3',  period: 15,   note: 'p15' },
    { id: 'block',              name: 'Block',              cat: 'still life',   size: '2×2',   period: 1,    note: 'still' },
    { id: 'beehive',            name: 'Beehive',            cat: 'still life',   size: '4×3',   period: 1,    note: 'still' },
    { id: 'loaf',               name: 'Loaf',               cat: 'still life',   size: '4×4',   period: 1,    note: 'still' },
    { id: 'boat',               name: 'Boat',               cat: 'still life',   size: '3×3',   period: 1,    note: 'still' },
    { id: 'tub',                name: 'Tub',                cat: 'still life',   size: '3×3',   period: 1,    note: 'still' },
    { id: 'r_pentomino',        name: 'R-pentomino',        cat: 'methuselah',   size: '3×3',   period: null, note: '~1103 gens' },
    { id: 'acorn',              name: 'Acorn',              cat: 'methuselah',   size: '7×3',   period: null, note: '~5206 gens' },
    { id: 'diehard',            name: 'Diehard',            cat: 'methuselah',   size: '8×3',   period: null, note: 'dies @ 130' },
    { id: 'bunnies',            name: 'Bunnies',            cat: 'methuselah',   size: '8×4',   period: null, note: '~17331 gens' },
    { id: 'gosper_glider_gun',  name: 'Gosper Gun',         cat: 'gun',          size: '36×9',  period: 30,   note: 'p30 emitter' },
    { id: 'eater',              name: 'Eater 1',            cat: 'exotic',       size: '4×4',   period: 1,    note: 'consumer' },
  ];

  const RULE_PRESETS = [
    { id: 'B3/S23',         name: 'Conway',          note: 'standard' },
    { id: 'B36/S23',        name: 'HighLife',        note: 'replicator' },
    { id: 'B2/S',           name: 'Seeds',           note: 'no survival' },
    { id: 'B1/S1',          name: 'Gnarl',           note: 'expansive' },
    { id: 'B3/S012345678',  name: 'Life w/o Death',  note: 'never dies' },
    { id: 'B34/S34',        name: '34 Life',         note: 'symmetric' },
    { id: 'B3678/S34678',   name: 'Day & Night',     note: 'self-dual' },
    { id: 'B5678/S45678',   name: 'Diamoeba',        note: 'amorphous' },
  ];

  window.LifeBoard = LifeBoard;
  window.LIFE_PATTERNS = P;
  window.PATTERN_META = PATTERN_META;
  window.RULE_PRESETS = RULE_PRESETS;
})();
