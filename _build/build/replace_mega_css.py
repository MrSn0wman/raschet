# -*- coding: utf-8 -*-
# Замена блока мега-меню (строки 504-571) в parts/style.css на hover-дропдауны категорий.
import io

P = r"C:\Kimi\raschet\_build\parts\style.css"
lines = io.open(P, encoding="utf-8").read().split("\n")

# границы по маркерам (устойчивее номеров строк)
start = next(i for i, l in enumerate(lines) if l.startswith("/* ---------- v2: мега-меню"))
end = next(i for i, l in enumerate(lines) if l.startswith("/* ---------- v2: действия шапки"))

NEW_BLOCK = """/* ---------- v3: категории в шапке (hover-дропдауны) ---------- */
.nav-cat{ position:relative; }
.nav-cat-btn{
  display:inline-flex; align-items:center; gap:6px;
  background:none; border:none; cursor:pointer;
  font-family:var(--font-body); color:var(--ink-soft);
  font-size:.93rem; font-weight:500;
  padding:9px 12px; min-height:44px; border-radius:8px;
  transition:color .15s ease, background .15s ease;
  white-space:nowrap;
}
.nav-cat-btn:hover, .nav-cat.open .nav-cat-btn{ color:var(--accent); background:var(--surface); }
.nav-cat-btn .chev{ transition:transform .18s ease; flex:none; }
.nav-cat.open .nav-cat-btn .chev{ transform:rotate(180deg); }

.nav-cat-panel{
  position:absolute; top:calc(100% + 6px); left:0;
  min-width:240px;
  background:var(--surface); border:1px solid var(--line);
  border-radius:var(--radius-m); box-shadow:var(--shadow-pop);
  padding:8px; display:grid; gap:2px;
  opacity:0; visibility:hidden; transform:translateY(-6px);
  transition:opacity .16s ease, transform .16s ease, visibility .16s;
  z-index:110;
}
.nav-cat:last-child .nav-cat-panel,
.nav-cat:nth-last-child(2) .nav-cat-panel{ left:auto; right:0; }
.nav-cat.open .nav-cat-panel{ opacity:1; visibility:visible; transform:translateY(0); }
.nav-cat-panel a{
  display:block; text-decoration:none; color:var(--ink);
  font-size:.92rem; padding:9px 12px; border-radius:8px; line-height:1.3;
  transition:background .12s ease, color .12s ease;
}
.nav-cat-panel a:hover{ background:var(--surface-2); color:var(--accent); }

"""

lines[start:end] = NEW_BLOCK.split("\n") + [""]
io.open(P, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print("mega block replaced:", start, "->", end, "; new lines:", len(NEW_BLOCK.split(chr(10))))
