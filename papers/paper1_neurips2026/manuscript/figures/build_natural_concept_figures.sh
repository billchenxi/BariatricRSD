#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/paper/figures"
SUB="$ROOT/paper/Formatting_Instructions_For_NeurIPS_2026/figures"

mkdir -p "$OUT" "$SUB"

FRAME_DIR="$ROOT/lambda_mirror/extern/MultiBypass140/datasets/MultiBypass140/BernBypass70/frames/BBP12"
F1="$(base64 < "$FRAME_DIR/BBP12_00003439.jpg" | tr -d '\n')"
F2="$(base64 < "$FRAME_DIR/BBP12_00003444.jpg" | tr -d '\n')"
F3="$(base64 < "$FRAME_DIR/BBP12_00003449.jpg" | tr -d '\n')"
F4="$(base64 < "$FRAME_DIR/BBP12_00003454.jpg" | tr -d '\n')"
F5="$(base64 < "$FRAME_DIR/BBP12_00003459.jpg" | tr -d '\n')"
F6="$(base64 < "$FRAME_DIR/BBP12_00003464.jpg" | tr -d '\n')"
F7="$(base64 < "$FRAME_DIR/BBP12_00003469.jpg" | tr -d '\n')"
F8="$(base64 < "$FRAME_DIR/BBP12_00003474.jpg" | tr -d '\n')"

render_one() {
  local svg="$1"
  sips -s format png "$svg" --out "${svg%.svg}.png" >/dev/null
  cp -p "$svg" "$SUB/$(basename "$svg")"
  cp -p "${svg%.svg}.png" "$SUB/$(basename "${svg%.svg}.png")"
}

common_defs() {
  cat <<'SVG'
  <defs>
    <style>
      .title{font-family:Avenir Next,Arial,sans-serif;font-size:46px;font-weight:800;fill:#111827}
      .subtitle{font-family:Avenir Next,Arial,sans-serif;font-size:24px;font-weight:500;fill:#4b5563}
      .label{font-family:Avenir Next,Arial,sans-serif;font-size:22px;font-weight:700;fill:#111827}
      .body{font-family:Avenir Next,Arial,sans-serif;font-size:19px;font-weight:500;fill:#374151}
      .small{font-family:Avenir Next,Arial,sans-serif;font-size:16px;font-weight:500;fill:#4b5563}
      .tiny{font-family:Avenir Next,Arial,sans-serif;font-size:13px;font-weight:600;fill:#4b5563}
      .white{font-family:Avenir Next,Arial,sans-serif;font-size:22px;font-weight:800;fill:white}
      .cap{font-family:Avenir Next,Arial,sans-serif;font-size:18px;font-weight:700;fill:#111827}
      .note{font-family:Avenir Next,Arial,sans-serif;font-size:20px;font-weight:700;fill:#0f172a}
      .soft{fill:#ffffff;stroke:#d1d5db;stroke-width:2}
      .past{fill:#dbeafe;stroke:#2563eb;stroke-width:3}
      .now{fill:#fff7ed;stroke:#f59e0b;stroke-width:4}
      .future{fill:#fee2e2;stroke:#dc2626;stroke-width:3}
    </style>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.13"/>
    </filter>
    <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="3" stdDeviation="5" flood-color="#0f172a" flood-opacity="0.10"/>
    </filter>
    <marker id="arrow" markerWidth="16" markerHeight="16" refX="14" refY="8" orient="auto">
      <path d="M0,0 L16,8 L0,16 Z" fill="#334155"/>
    </marker>
    <marker id="arrowGreen" markerWidth="16" markerHeight="16" refX="14" refY="8" orient="auto">
      <path d="M0,0 L16,8 L0,16 Z" fill="#0f766e"/>
    </marker>
    <marker id="arrowOrange" markerWidth="16" markerHeight="16" refX="14" refY="8" orient="auto">
      <path d="M0,0 L16,8 L0,16 Z" fill="#ea580c"/>
    </marker>
  </defs>
SVG
}

svg1="$OUT/fig_concept01_workflow_variation.svg"
cat > "$svg1" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
$(common_defs)
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="78" class="title">Concept 1: same operation, different workflow routes</text>
  <text x="72" y="120" class="subtitle">RSD is hard because phase order and case duration vary across centers and cases.</text>

  <clipPath id="p1"><rect x="70" y="170" width="300" height="180" rx="22"/></clipPath>
  <clipPath id="p2"><rect x="1228" y="170" width="300" height="180" rx="22"/></clipPath>
  <rect x="70" y="170" width="300" height="180" rx="22" fill="#fff" filter="url(#shadow)"/>
  <image x="70" y="170" width="300" height="180" href="data:image/jpeg;base64,$F1" preserveAspectRatio="xMidYMid slice" clip-path="url(#p1)"/>
  <rect x="70" y="170" width="300" height="180" rx="22" fill="none" stroke="#2563eb" stroke-width="5"/>
  <text x="92" y="388" class="label">Case family A</text>
  <text x="92" y="418" class="small">shorter, one phase order</text>
  <rect x="1228" y="170" width="300" height="180" rx="22" fill="#fff" filter="url(#shadow)"/>
  <image x="1228" y="170" width="300" height="180" href="data:image/jpeg;base64,$F5" preserveAspectRatio="xMidYMid slice" clip-path="url(#p2)"/>
  <rect x="1228" y="170" width="300" height="180" rx="22" fill="none" stroke="#0f766e" stroke-width="5"/>
  <text x="1250" y="388" class="label">Case family B</text>
  <text x="1250" y="418" class="small">longer, different phase order</text>

  <path d="M255 575 C410 430, 560 450, 700 555 S1010 700, 1320 510" fill="none" stroke="#bfdbfe" stroke-width="48" stroke-linecap="round"/>
  <path d="M255 575 C410 430, 560 450, 700 555 S1010 700, 1320 510" fill="none" stroke="#2563eb" stroke-width="8" stroke-linecap="round"/>
  <path d="M255 720 C420 640, 520 760, 710 700 S1005 460, 1325 650" fill="none" stroke="#ccfbf1" stroke-width="48" stroke-linecap="round"/>
  <path d="M255 720 C420 640, 520 760, 710 700 S1005 460, 1325 650" fill="none" stroke="#0f766e" stroke-width="8" stroke-linecap="round"/>

  <g filter="url(#softShadow)">
    <rect x="360" y="395" width="170" height="64" rx="32" fill="#eff6ff" stroke="#2563eb" stroke-width="3"/>
    <text x="445" y="436" text-anchor="middle" class="cap">pouch</text>
    <rect x="600" y="492" width="150" height="64" rx="32" fill="#eff6ff" stroke="#2563eb" stroke-width="3"/>
    <text x="675" y="533" text-anchor="middle" class="cap">GJ</text>
    <rect x="850" y="646" width="150" height="64" rx="32" fill="#eff6ff" stroke="#2563eb" stroke-width="3"/>
    <text x="925" y="687" text-anchor="middle" class="cap">JJ</text>
    <rect x="1180" y="510" width="175" height="64" rx="32" fill="#eff6ff" stroke="#2563eb" stroke-width="3"/>
    <text x="1268" y="551" text-anchor="middle" class="cap">closure</text>

    <rect x="350" y="650" width="170" height="64" rx="32" fill="#ecfdf5" stroke="#0f766e" stroke-width="3"/>
    <text x="435" y="691" text-anchor="middle" class="cap">pouch</text>
    <rect x="608" y="720" width="150" height="64" rx="32" fill="#ecfdf5" stroke="#0f766e" stroke-width="3"/>
    <text x="683" y="761" text-anchor="middle" class="cap">JJ</text>
    <rect x="880" y="494" width="150" height="64" rx="32" fill="#ecfdf5" stroke="#0f766e" stroke-width="3"/>
    <text x="955" y="535" text-anchor="middle" class="cap">GJ</text>
    <rect x="1162" y="655" width="175" height="64" rx="32" fill="#ecfdf5" stroke="#0f766e" stroke-width="3"/>
    <text x="1250" y="696" text-anchor="middle" class="cap">closure</text>
  </g>

  <rect x="472" y="815" width="660" height="72" rx="24" fill="#ffffff" stroke="#e5e7eb" stroke-width="2" filter="url(#softShadow)"/>
  <text x="802" y="846" text-anchor="middle" class="note">The workflow token gives the model a route context.</text>
  <text x="802" y="874" text-anchor="middle" class="small">Without it, the RSD head averages across routes that can mean different remaining times.</text>
</svg>
SVG

svg2="$OUT/fig_concept02_oracle_vs_prefix.svg"
cat > "$svg2" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
$(common_defs)
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="78" class="title">Concept 2: retrospective oracle versus live prefix</text>
  <text x="72" y="120" class="subtitle">The oracle knows the whole case; the deployable path estimates workflow style from what has happened so far.</text>

  <rect x="78" y="175" width="680" height="640" rx="34" fill="#fff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>
  <rect x="842" y="175" width="680" height="640" rx="34" fill="#fff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>
  <text x="120" y="232" class="label">Retrospective oracle</text>
  <text x="884" y="232" class="label">Causal-at-inference</text>
  <text x="120" y="265" class="small">after the operation, full phase sequence is known</text>
  <text x="884" y="265" class="small">during the operation, only the observed prefix is visible</text>

  <g>
    <rect x="120" y="315" width="74" height="390" rx="28" fill="#e0f2fe"/>
    <rect x="210" y="315" width="74" height="390" rx="28" fill="#bfdbfe"/>
    <rect x="300" y="315" width="74" height="390" rx="28" fill="#c7d2fe"/>
    <rect x="390" y="315" width="74" height="390" rx="28" fill="#ddd6fe"/>
    <rect x="480" y="315" width="74" height="390" rx="28" fill="#fed7aa"/>
    <rect x="570" y="315" width="74" height="390" rx="28" fill="#fecaca"/>
    <text x="382" y="744" text-anchor="middle" class="small">full phase order: start to finish</text>
    <path d="M205 514 C300 448, 418 455, 512 514 S650 590, 678 520" fill="none" stroke="#64748b" stroke-width="5" stroke-linecap="round"/>
    <rect x="268" y="366" width="235" height="90" rx="24" fill="#0f172a"/>
    <text x="386" y="404" text-anchor="middle" class="white">hard workflow</text>
    <text x="386" y="435" text-anchor="middle" class="white">cluster z = 4</text>
    <text x="382" y="785" text-anchor="middle" class="body">Diagnostic upper bound, not live input.</text>
  </g>

  <g>
    <clipPath id="live1"><rect x="894" y="320" width="118" height="88" rx="14"/></clipPath>
    <clipPath id="live2"><rect x="1026" y="320" width="118" height="88" rx="14"/></clipPath>
    <clipPath id="live3"><rect x="1158" y="320" width="118" height="88" rx="14"/></clipPath>
    <clipPath id="live4"><rect x="1290" y="320" width="118" height="88" rx="14"/></clipPath>
    <image x="894" y="320" width="118" height="88" href="data:image/jpeg;base64,$F1" preserveAspectRatio="xMidYMid slice" clip-path="url(#live1)"/>
    <image x="1026" y="320" width="118" height="88" href="data:image/jpeg;base64,$F2" preserveAspectRatio="xMidYMid slice" clip-path="url(#live2)"/>
    <image x="1158" y="320" width="118" height="88" href="data:image/jpeg;base64,$F3" preserveAspectRatio="xMidYMid slice" clip-path="url(#live3)"/>
    <image x="1290" y="320" width="118" height="88" href="data:image/jpeg;base64,$F4" preserveAspectRatio="xMidYMid slice" clip-path="url(#live4)"/>
    <rect x="894" y="320" width="118" height="88" rx="14" fill="none" stroke="#2563eb" stroke-width="4"/>
    <rect x="1026" y="320" width="118" height="88" rx="14" fill="none" stroke="#2563eb" stroke-width="4"/>
    <rect x="1158" y="320" width="118" height="88" rx="14" fill="none" stroke="#2563eb" stroke-width="4"/>
    <rect x="1290" y="320" width="118" height="88" rx="14" fill="none" stroke="#f59e0b" stroke-width="5"/>
    <rect x="1422" y="320" width="58" height="88" rx="14" fill="#e5e7eb"/>
    <text x="1451" y="372" text-anchor="middle" class="tiny">future</text>
    <text x="1187" y="442" text-anchor="middle" class="small">prefix frames and model-predicted phases</text>

    <path d="M1175 475 C1130 540, 1105 590, 1088 650" fill="none" stroke="#0f766e" stroke-width="8" stroke-linecap="round" marker-end="url(#arrowGreen)"/>
    <path d="M1250 475 C1330 548, 1365 595, 1385 650" fill="none" stroke="#0f766e" stroke-width="8" stroke-linecap="round" marker-end="url(#arrowGreen)"/>
    <rect x="1000" y="645" width="420" height="95" rx="32" fill="#ecfdf5" stroke="#0f766e" stroke-width="3"/>
    <text x="1210" y="685" text-anchor="middle" class="label">soft posterior q</text>
    <text x="1210" y="718" text-anchor="middle" class="small">uncertain mixture over workflow families</text>
    <text x="1210" y="785" text-anchor="middle" class="body">No GT phase labels or full-case cluster labels at inference.</text>
  </g>
</svg>
SVG

svg3="$OUT/fig_concept03_workflow_signature.svg"
cat > "$svg3" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
  <defs>
    <style>
      .title{font-family:Avenir Next,Arial,sans-serif;font-size:46px;font-weight:800;fill:#111827}
      .subtitle{font-family:Avenir Next,Arial,sans-serif;font-size:24px;font-weight:500;fill:#4b5563}
      .label{font-family:Avenir Next,Arial,sans-serif;font-size:22px;font-weight:700;fill:#111827}
      .body{font-family:Avenir Next,Arial,sans-serif;font-size:19px;font-weight:500;fill:#374151}
      .small{font-family:Avenir Next,Arial,sans-serif;font-size:16px;font-weight:500;fill:#4b5563}
      .cap{font-family:Avenir Next,Arial,sans-serif;font-size:18px;font-weight:700;fill:#111827}
    </style>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.12"/>
    </filter>
    <marker id="arrow" markerWidth="16" markerHeight="16" refX="14" refY="8" orient="auto">
      <path d="M0,0 L16,8 L0,16 Z" fill="#334155"/>
    </marker>
  </defs>
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="78" class="title">Concept 3: turn a phase story into a workflow family</text>
  <text x="72" y="120" class="subtitle">The cluster is not a duration bin; it is a summary of phase-order transitions.</text>

  <rect x="72" y="178" width="1456" height="630" rx="34" fill="#ffffff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>

  <path d="M155 310 C250 240, 345 378, 440 306 S640 288, 715 348" fill="none" stroke="#cbd5e1" stroke-width="9" stroke-linecap="round"/>
  <g>
    <circle cx="160" cy="310" r="34" fill="#bfdbfe" stroke="#2563eb" stroke-width="3"/><text x="160" y="317" text-anchor="middle" class="cap">A</text>
    <circle cx="255" cy="265" r="34" fill="#bfdbfe" stroke="#2563eb" stroke-width="3"/><text x="255" y="272" text-anchor="middle" class="cap">A</text>
    <circle cx="350" cy="350" r="34" fill="#ccfbf1" stroke="#0f766e" stroke-width="3"/><text x="350" y="357" text-anchor="middle" class="cap">B</text>
    <circle cx="450" cy="305" r="34" fill="#ccfbf1" stroke="#0f766e" stroke-width="3"/><text x="450" y="312" text-anchor="middle" class="cap">B</text>
    <circle cx="555" cy="292" r="34" fill="#fed7aa" stroke="#ea580c" stroke-width="3"/><text x="555" y="299" text-anchor="middle" class="cap">C</text>
    <circle cx="670" cy="338" r="34" fill="#e9d5ff" stroke="#7c3aed" stroke-width="3"/><text x="670" y="345" text-anchor="middle" class="cap">D</text>
  </g>
  <text x="405" y="430" text-anchor="middle" class="label">phase sequence</text>
  <text x="405" y="460" text-anchor="middle" class="small">collapse repeats: A, A, B, B, C, D -> A, B, C, D</text>

  <path d="M755 330 C835 330, 865 330, 930 330" fill="none" stroke="#334155" stroke-width="5" marker-end="url(#arrow)"/>
  <g>
    <rect x="960" y="235" width="120" height="54" rx="27" fill="#eef2ff" stroke="#4f46e5" stroke-width="2"/><text x="1020" y="270" text-anchor="middle" class="cap">A->B</text>
    <rect x="1095" y="305" width="120" height="54" rx="27" fill="#eef2ff" stroke="#4f46e5" stroke-width="2"/><text x="1155" y="340" text-anchor="middle" class="cap">B->C</text>
    <rect x="1230" y="235" width="120" height="54" rx="27" fill="#eef2ff" stroke="#4f46e5" stroke-width="2"/><text x="1290" y="270" text-anchor="middle" class="cap">C->D</text>
    <text x="1155" y="430" text-anchor="middle" class="label">transition bigrams</text>
    <text x="1155" y="460" text-anchor="middle" class="small">TF-IDF weights transitions by how distinctive they are</text>
  </g>

  <path d="M330 555 C470 665, 560 515, 690 650" fill="none" stroke="#334155" stroke-width="5" marker-end="url(#arrow)"/>
  <rect x="735" y="535" width="600" height="220" rx="30" fill="#f8fafc" stroke="#d1d5db" stroke-width="2"/>
  <text x="1035" y="575" text-anchor="middle" class="label">PCA map + k-means islands</text>
  <ellipse cx="880" cy="665" rx="95" ry="45" fill="#bfdbfe" opacity=".7"/>
  <ellipse cx="1040" cy="660" rx="115" ry="50" fill="#ccfbf1" opacity=".72"/>
  <ellipse cx="1210" cy="666" rx="85" ry="42" fill="#fed7aa" opacity=".75"/>
  <g fill="#111827" opacity=".72">
    <circle cx="840" cy="650" r="7"/><circle cx="890" cy="670" r="7"/><circle cx="920" cy="645" r="7"/>
    <circle cx="1005" cy="665" r="7"/><circle cx="1068" cy="641" r="7"/><circle cx="1098" cy="685" r="7"/>
    <circle cx="1190" cy="650" r="7"/><circle cx="1234" cy="675" r="7"/>
  </g>
  <text x="1035" y="725" text-anchor="middle" class="small">Each island becomes one learned workflow token row E[k,:]</text>

  <rect x="150" y="645" width="475" height="112" rx="24" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
  <text x="178" y="684" class="label">What the token means</text>
  <text x="178" y="716" class="body">A procedural pattern, not the raw phase labels and not the final duration.</text>
</svg>
SVG

svg4="$OUT/fig_concept04_soft_token_inference.svg"
cat > "$svg4" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
$(common_defs)
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="78" class="title">Concept 4: soft workflow token from the prefix</text>
  <text x="72" y="120" class="subtitle">Inference reads model-predicted phases, converts them to a posterior, then blends learned workflow embeddings.</text>

  <clipPath id="a1"><rect x="82" y="172" width="166" height="118" rx="16"/></clipPath>
  <clipPath id="a2"><rect x="262" y="172" width="166" height="118" rx="16"/></clipPath>
  <clipPath id="a3"><rect x="442" y="172" width="166" height="118" rx="16"/></clipPath>
  <clipPath id="a4"><rect x="622" y="172" width="166" height="118" rx="16"/></clipPath>
  <clipPath id="a5"><rect x="802" y="172" width="166" height="118" rx="16"/></clipPath>
  <image x="82" y="172" width="166" height="118" href="data:image/jpeg;base64,$F1" preserveAspectRatio="xMidYMid slice" clip-path="url(#a1)"/>
  <image x="262" y="172" width="166" height="118" href="data:image/jpeg;base64,$F2" preserveAspectRatio="xMidYMid slice" clip-path="url(#a2)"/>
  <image x="442" y="172" width="166" height="118" href="data:image/jpeg;base64,$F3" preserveAspectRatio="xMidYMid slice" clip-path="url(#a3)"/>
  <image x="622" y="172" width="166" height="118" href="data:image/jpeg;base64,$F4" preserveAspectRatio="xMidYMid slice" clip-path="url(#a4)"/>
  <image x="802" y="172" width="166" height="118" href="data:image/jpeg;base64,$F5" preserveAspectRatio="xMidYMid slice" clip-path="url(#a5)"/>
  <g fill="none" stroke-width="4"><rect x="82" y="172" width="166" height="118" rx="16" stroke="#2563eb"/><rect x="262" y="172" width="166" height="118" rx="16" stroke="#2563eb"/><rect x="442" y="172" width="166" height="118" rx="16" stroke="#2563eb"/><rect x="622" y="172" width="166" height="118" rx="16" stroke="#2563eb"/><rect x="802" y="172" width="166" height="118" rx="16" stroke="#f59e0b"/></g>
  <text x="525" y="330" text-anchor="middle" class="label">observed prefix frames</text>

  <path d="M970 235 C1060 260, 1110 310, 1160 376" fill="none" stroke="#334155" stroke-width="5" marker-end="url(#arrow)"/>
  <g filter="url(#softShadow)">
    <rect x="136" y="410" width="180" height="60" rx="30" fill="#eff6ff" stroke="#2563eb" stroke-width="3"/><text x="226" y="449" text-anchor="middle" class="cap">prep</text>
    <rect x="350" y="410" width="180" height="60" rx="30" fill="#ecfdf5" stroke="#0f766e" stroke-width="3"/><text x="440" y="449" text-anchor="middle" class="cap">gastric</text>
    <rect x="564" y="410" width="180" height="60" rx="30" fill="#ecfdf5" stroke="#0f766e" stroke-width="3"/><text x="654" y="449" text-anchor="middle" class="cap">omentum</text>
    <rect x="778" y="410" width="180" height="60" rx="30" fill="#fff7ed" stroke="#f59e0b" stroke-width="3"/><text x="868" y="449" text-anchor="middle" class="cap">GJ</text>
  </g>
  <path d="M316 440 H350 M530 440 H564 M744 440 H778" stroke="#94a3b8" stroke-width="5" stroke-linecap="round"/>
  <text x="548" y="515" text-anchor="middle" class="small">argmax phase labels form the prefix phase sequence</text>

  <rect x="1050" y="380" width="430" height="240" rx="34" fill="#f5f3ff" stroke="#7c3aed" stroke-width="3" filter="url(#shadow)"/>
  <text x="1265" y="430" text-anchor="middle" class="label">posterior over workflow families</text>
  <line x1="1120" y1="545" x2="1410" y2="545" stroke="#94a3b8" stroke-width="3"/>
  <rect x="1130" y="530" width="24" height="15" fill="#a78bfa"/><rect x="1180" y="536" width="24" height="9" fill="#a78bfa"/><rect x="1230" y="536" width="24" height="9" fill="#a78bfa"/><rect x="1280" y="530" width="24" height="15" fill="#a78bfa"/><rect x="1330" y="455" width="38" height="90" fill="#7c3aed"/><rect x="1388" y="540" width="24" height="5" fill="#a78bfa"/>
  <text x="1138" y="578" text-anchor="middle" class="tiny">C0</text><text x="1192" y="578" text-anchor="middle" class="tiny">C1</text><text x="1242" y="578" text-anchor="middle" class="tiny">C2</text><text x="1292" y="578" text-anchor="middle" class="tiny">C3</text><text x="1349" y="578" text-anchor="middle" class="tiny">C4</text><text x="1400" y="578" text-anchor="middle" class="tiny">C5</text>
  <text x="1349" y="650" text-anchor="middle" class="body">q4 dominates, but uncertainty is kept</text>

  <path d="M1240 620 C1160 700, 1020 715, 855 760" stroke="#7c3aed" stroke-width="18" opacity=".30" fill="none"/>
  <path d="M1320 620 C1160 725, 1030 752, 855 790" stroke="#f59e0b" stroke-width="14" opacity=".45" fill="none"/>
  <path d="M1380 620 C1180 755, 1050 810, 855 822" stroke="#2563eb" stroke-width="9" opacity=".22" fill="none"/>
  <rect x="380" y="720" width="475" height="138" rx="34" fill="#fff7ed" stroke="#f59e0b" stroke-width="4" filter="url(#shadow)"/>
  <text x="618" y="770" text-anchor="middle" class="label">soft workflow token</text>
  <text x="618" y="808" text-anchor="middle" class="body">e_z = sum q_k E[k,:]</text>
  <text x="618" y="842" text-anchor="middle" class="small">replace placeholder, re-run temporal/RSD head</text>
</svg>
SVG

svg5="$OUT/fig_concept05_protocol_caveat.svg"
cat > "$svg5" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
$(common_defs)
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="78" class="title">Concept 5: the centered-window caveat</text>
  <text x="72" y="120" class="subtitle">The workflow token can be prefix-derived while the visual clip itself still contains post-target frames.</text>

  <rect x="92" y="190" width="1418" height="250" rx="30" fill="#ffffff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>
  <text x="130" y="245" class="label">Strict prefix-only clip</text>
  <text x="130" y="278" class="small">target is the last frame</text>
  <g transform="translate(420 230)">
    <rect x="0" y="0" width="120" height="90" rx="15" class="past"/><text x="60" y="54" text-anchor="middle" class="cap">t-35</text>
    <rect x="140" y="0" width="120" height="90" rx="15" class="past"/><text x="200" y="54" text-anchor="middle" class="cap">t-30</text>
    <rect x="280" y="0" width="120" height="90" rx="15" class="past"/><text x="340" y="54" text-anchor="middle" class="cap">t-25</text>
    <rect x="420" y="0" width="120" height="90" rx="15" class="past"/><text x="480" y="54" text-anchor="middle" class="cap">t-20</text>
    <rect x="560" y="0" width="120" height="90" rx="15" class="past"/><text x="620" y="54" text-anchor="middle" class="cap">t-15</text>
    <rect x="700" y="0" width="120" height="90" rx="15" class="past"/><text x="760" y="54" text-anchor="middle" class="cap">t-10</text>
    <rect x="840" y="0" width="120" height="90" rx="15" class="past"/><text x="900" y="54" text-anchor="middle" class="cap">t-5</text>
    <rect x="980" y="0" width="120" height="90" rx="15" class="now"/><text x="1040" y="54" text-anchor="middle" class="cap">t</text>
  </g>
  <text x="970" y="365" text-anchor="middle" class="body">real-time claim: no visual future</text>

  <rect x="92" y="510" width="1418" height="295" rx="30" fill="#ffffff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>
  <text x="130" y="565" class="label">Centered-window clip</text>
  <text x="130" y="598" class="small">The target timestamp sits in the middle; right-hand frames are after t.</text>
  <g transform="translate(252 642)">
    <clipPath id="c1"><rect x="0" y="0" width="142" height="100" rx="15"/></clipPath>
    <clipPath id="c2"><rect x="158" y="0" width="142" height="100" rx="15"/></clipPath>
    <clipPath id="c3"><rect x="316" y="0" width="142" height="100" rx="15"/></clipPath>
    <clipPath id="c4"><rect x="474" y="0" width="142" height="100" rx="15"/></clipPath>
    <clipPath id="c5"><rect x="632" y="0" width="142" height="100" rx="15"/></clipPath>
    <clipPath id="c6"><rect x="790" y="0" width="142" height="100" rx="15"/></clipPath>
    <clipPath id="c7"><rect x="948" y="0" width="142" height="100" rx="15"/></clipPath>
    <clipPath id="c8"><rect x="1106" y="0" width="142" height="100" rx="15"/></clipPath>
    <image x="0" y="0" width="142" height="100" href="data:image/jpeg;base64,$F1" preserveAspectRatio="xMidYMid slice" clip-path="url(#c1)"/>
    <image x="158" y="0" width="142" height="100" href="data:image/jpeg;base64,$F2" preserveAspectRatio="xMidYMid slice" clip-path="url(#c2)"/>
    <image x="316" y="0" width="142" height="100" href="data:image/jpeg;base64,$F3" preserveAspectRatio="xMidYMid slice" clip-path="url(#c3)"/>
    <image x="474" y="0" width="142" height="100" href="data:image/jpeg;base64,$F4" preserveAspectRatio="xMidYMid slice" clip-path="url(#c4)"/>
    <image x="632" y="0" width="142" height="100" href="data:image/jpeg;base64,$F5" preserveAspectRatio="xMidYMid slice" clip-path="url(#c5)"/>
    <image x="790" y="0" width="142" height="100" href="data:image/jpeg;base64,$F6" preserveAspectRatio="xMidYMid slice" clip-path="url(#c6)"/>
    <image x="948" y="0" width="142" height="100" href="data:image/jpeg;base64,$F7" preserveAspectRatio="xMidYMid slice" clip-path="url(#c7)"/>
    <image x="1106" y="0" width="142" height="100" href="data:image/jpeg;base64,$F8" preserveAspectRatio="xMidYMid slice" clip-path="url(#c8)"/>
    <g fill="none" stroke-width="5">
      <rect x="0" y="0" width="142" height="100" rx="15" stroke="#2563eb"/><rect x="158" y="0" width="142" height="100" rx="15" stroke="#2563eb"/><rect x="316" y="0" width="142" height="100" rx="15" stroke="#2563eb"/><rect x="474" y="0" width="142" height="100" rx="15" stroke="#2563eb"/>
      <rect x="632" y="0" width="142" height="100" rx="15" stroke="#f59e0b"/><rect x="790" y="0" width="142" height="100" rx="15" stroke="#dc2626"/><rect x="948" y="0" width="142" height="100" rx="15" stroke="#dc2626"/><rect x="1106" y="0" width="142" height="100" rx="15" stroke="#dc2626"/>
    </g>
    <text x="71" y="-14" text-anchor="middle" class="tiny">t-20</text><text x="229" y="-14" text-anchor="middle" class="tiny">t-15</text><text x="387" y="-14" text-anchor="middle" class="tiny">t-10</text><text x="545" y="-14" text-anchor="middle" class="tiny">t-5</text><text x="703" y="-14" text-anchor="middle" class="tiny">t</text><text x="861" y="-14" text-anchor="middle" class="tiny">t+5</text><text x="1019" y="-14" text-anchor="middle" class="tiny">t+10</text><text x="1177" y="-14" text-anchor="middle" class="tiny">t+15</text>
  </g>
  <text x="878" y="785" text-anchor="middle" class="note">This is why strict prefix-only and centered-window numbers have different scope.</text>
</svg>
SVG

svg6="$OUT/fig_concept06_decoupled_phase_head.svg"
cat > "$svg6" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
$(common_defs)
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="78" class="title">Concept 6: decouple phase prediction from workflow identity</text>
  <text x="72" y="120" class="subtitle">The phase head must read visual evidence before the workflow token can influence the temporal representation.</text>

  <clipPath id="lens"><rect x="98" y="210" width="300" height="210" rx="34"/></clipPath>
  <rect x="98" y="210" width="300" height="210" rx="34" fill="#fff" filter="url(#shadow)"/>
  <image x="98" y="210" width="300" height="210" href="data:image/jpeg;base64,$F3" preserveAspectRatio="xMidYMid slice" clip-path="url(#lens)"/>
  <rect x="98" y="210" width="300" height="210" rx="34" fill="none" stroke="#2563eb" stroke-width="5"/>
  <text x="248" y="465" text-anchor="middle" class="label">visual prefix</text>

  <path d="M410 315 C540 250, 690 250, 820 310" fill="none" stroke="#dbeafe" stroke-width="38" stroke-linecap="round"/>
  <path d="M410 315 C540 250, 690 250, 820 310" fill="none" stroke="#2563eb" stroke-width="7" stroke-linecap="round" marker-end="url(#arrow)"/>
  <rect x="830" y="240" width="270" height="135" rx="30" fill="#ecfdf5" stroke="#0f766e" stroke-width="4" filter="url(#softShadow)"/>
  <text x="965" y="290" text-anchor="middle" class="label">phase head</text>
  <text x="965" y="325" text-anchor="middle" class="body">visual features only</text>
  <text x="965" y="358" text-anchor="middle" class="small">source for prefix phases</text>

  <path d="M410 360 C560 490, 700 555, 865 598" fill="none" stroke="#ede9fe" stroke-width="42" stroke-linecap="round"/>
  <path d="M410 360 C560 490, 700 555, 865 598" fill="none" stroke="#7c3aed" stroke-width="7" stroke-linecap="round"/>
  <rect x="166" y="605" width="300" height="112" rx="34" fill="#fff7ed" stroke="#f59e0b" stroke-width="4" filter="url(#softShadow)"/>
  <text x="316" y="652" text-anchor="middle" class="label">workflow token</text>
  <text x="316" y="686" text-anchor="middle" class="small">oracle or soft prefix mixture</text>
  <path d="M466 660 C585 630, 730 615, 865 598" fill="none" stroke="#f59e0b" stroke-width="8" stroke-linecap="round" marker-end="url(#arrowOrange)"/>

  <rect x="875" y="535" width="280" height="145" rx="32" fill="#f5f3ff" stroke="#7c3aed" stroke-width="4" filter="url(#softShadow)"/>
  <text x="1015" y="588" text-anchor="middle" class="label">HTA temporal head</text>
  <text x="1015" y="625" text-anchor="middle" class="body">frames + workflow token</text>
  <text x="1015" y="658" text-anchor="middle" class="small">feeds RSD prediction</text>

  <path d="M520 675 C635 540, 760 410, 900 356" fill="none" stroke="#dc2626" stroke-width="5" stroke-dasharray="12 9"/>
  <rect x="640" y="438" width="250" height="92" rx="28" fill="#fff1f2" stroke="#dc2626" stroke-width="3"/>
  <text x="765" y="475" text-anchor="middle" class="label">closed gate</text>
  <text x="765" y="506" text-anchor="middle" class="small">token cannot explain phase</text>

  <rect x="1195" y="298" width="270" height="310" rx="34" fill="#ffffff" stroke="#d1d5db" stroke-width="2" filter="url(#shadow)"/>
  <text x="1330" y="350" text-anchor="middle" class="label">Why it matters</text>
  <text x="1330" y="397" text-anchor="middle" class="body">The causal pipeline uses</text>
  <text x="1330" y="427" text-anchor="middle" class="body">phase predictions to infer</text>
  <text x="1330" y="457" text-anchor="middle" class="body">the workflow token.</text>
  <text x="1330" y="515" text-anchor="middle" class="body">If the token shaped</text>
  <text x="1330" y="545" text-anchor="middle" class="body">phase logits, the loop</text>
  <text x="1330" y="575" text-anchor="middle" class="body">would be circular.</text>
</svg>
SVG

svg7="$OUT/fig_concept07_variability_scaling.svg"
cat > "$svg7" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
  <defs>
    <style>
      .title{font-family:Avenir Next,Arial,sans-serif;font-size:46px;font-weight:800;fill:#111827}
      .subtitle{font-family:Avenir Next,Arial,sans-serif;font-size:24px;font-weight:500;fill:#4b5563}
      .label{font-family:Avenir Next,Arial,sans-serif;font-size:22px;font-weight:700;fill:#111827}
      .body{font-family:Avenir Next,Arial,sans-serif;font-size:19px;font-weight:500;fill:#374151}
      .small{font-family:Avenir Next,Arial,sans-serif;font-size:16px;font-weight:500;fill:#4b5563}
      .white{font-family:Avenir Next,Arial,sans-serif;font-size:20px;font-weight:800;fill:white}
    </style>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.12"/>
    </filter>
  </defs>
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="78" class="title">Concept 7: workflow conditioning scales with route diversity</text>
  <text x="72" y="120" class="subtitle">When most cases follow one template, the token adds little; when routes vary, it can reduce RSD error.</text>

  <rect x="95" y="180" width="1410" height="610" rx="36" fill="#ffffff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>
  <line x1="210" y1="695" x2="1360" y2="695" stroke="#1f2937" stroke-width="4"/>
  <line x1="210" y1="695" x2="210" y2="265" stroke="#1f2937" stroke-width="4"/>
  <text x="780" y="755" text-anchor="middle" class="label">workflow cluster entropy H(z)</text>
  <text x="85" y="475" text-anchor="middle" class="label" transform="rotate(-90 85 475)">workflow-token benefit</text>
  <text x="210" y="735" text-anchor="middle" class="small">low diversity</text>
  <text x="1360" y="735" text-anchor="middle" class="small">high diversity</text>

  <path d="M245 645 C430 650, 620 615, 820 520 S1130 350, 1320 315" fill="none" stroke="#0f766e" stroke-width="10" stroke-linecap="round"/>
  <path d="M250 655 C430 660, 615 640, 800 600" fill="none" stroke="#dc2626" stroke-width="5" stroke-dasharray="12 9"/>
  <circle cx="555" cy="625" r="18" fill="#ef4444"/><text x="460" y="618" text-anchor="end" class="label">Cholec80 prefix</text><text x="585" y="657" class="small">+0.42 min worse</text>
  <circle cx="555" cy="570" r="18" fill="#94a3b8"/><text x="555" y="535" text-anchor="middle" class="small">Cholec80 oracle null</text>
  <circle cx="1190" cy="410" r="20" fill="#0f766e"/><text x="1190" y="370" text-anchor="middle" class="label">MB140 cross-center</text><text x="1190" y="444" text-anchor="middle" class="small">-0.47 min</text>
  <circle cx="1280" cy="315" r="24" fill="#14b8a6"/><text x="1280" y="270" text-anchor="middle" class="label">MB140 fold 0</text><text x="1280" y="350" text-anchor="middle" class="small">-0.85 min</text>
  <circle cx="1110" cy="520" r="17" fill="#99f6e4" stroke="#0f766e" stroke-width="3"/><text x="1110" y="555" text-anchor="middle" class="small">5-fold avg -0.19</text>

  <rect x="275" y="305" width="270" height="150" rx="28" fill="#f1f5f9" stroke="#cbd5e1" stroke-width="2"/>
  <text x="410" y="350" text-anchor="middle" class="label">Cholec80</text>
  <text x="410" y="382" text-anchor="middle" class="body">51 / 12 / 6 / 3</text>
  <text x="410" y="414" text-anchor="middle" class="small">one cluster dominates</text>

  <rect x="1035" y="580" width="300" height="88" rx="28" fill="#ecfdf5" stroke="#0f766e" stroke-width="2"/>
  <text x="1185" y="615" text-anchor="middle" class="label">MB140</text>
  <text x="1185" y="648" text-anchor="middle" class="small">38 / 27 / 25 / 23 / 17 / 10</text>
</svg>
SVG

svg8="$OUT/fig_concept08_shuffled_token_control.svg"
cat > "$svg8" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
  <defs>
    <style>
      .title{font-family:Avenir Next,Arial,sans-serif;font-size:46px;font-weight:800;fill:#111827}
      .subtitle{font-family:Avenir Next,Arial,sans-serif;font-size:24px;font-weight:500;fill:#4b5563}
      .label{font-family:Avenir Next,Arial,sans-serif;font-size:22px;font-weight:700;fill:#111827}
      .body{font-family:Avenir Next,Arial,sans-serif;font-size:19px;font-weight:500;fill:#374151}
      .small{font-family:Avenir Next,Arial,sans-serif;font-size:16px;font-weight:500;fill:#4b5563}
      .white{font-family:Avenir Next,Arial,sans-serif;font-size:20px;font-weight:800;fill:white}
    </style>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="8" stdDeviation="10" flood-color="#0f172a" flood-opacity="0.12"/>
    </filter>
  </defs>
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="78" class="title">Concept 8: shuffled-token control</text>
  <text x="72" y="120" class="subtitle">If any extra learned vector helped, a shuffled workflow token would improve too. It does not.</text>

  <rect x="110" y="205" width="390" height="510" rx="34" fill="#ffffff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>
  <rect x="605" y="205" width="390" height="510" rx="34" fill="#ffffff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>
  <rect x="1100" y="205" width="390" height="510" rx="34" fill="#ffffff" stroke="#e5e7eb" stroke-width="2" filter="url(#shadow)"/>

  <text x="305" y="268" text-anchor="middle" class="label">No token</text>
  <text x="800" y="268" text-anchor="middle" class="label">Shuffled token</text>
  <text x="1295" y="268" text-anchor="middle" class="label">Real workflow token</text>

  <circle cx="305" cy="378" r="68" fill="#e5e7eb" stroke="#64748b" stroke-width="4"/><text x="305" y="386" text-anchor="middle" class="label">none</text>
  <path d="M735 344 L865 412 M865 344 L735 412" stroke="#dc2626" stroke-width="12" stroke-linecap="round"/>
  <rect x="720" y="322" width="160" height="112" rx="28" fill="none" stroke="#64748b" stroke-width="4"/>
  <circle cx="1295" cy="378" r="68" fill="#ccfbf1" stroke="#0f766e" stroke-width="5"/><text x="1295" y="370" text-anchor="middle" class="label">route</text><text x="1295" y="398" text-anchor="middle" class="label">ID</text>

  <line x1="190" y1="620" x2="1410" y2="620" stroke="#cbd5e1" stroke-width="3"/>
  <rect x="230" y="451" width="150" height="169" fill="#94a3b8"/><text x="305" y="646" text-anchor="middle" class="body">13.03</text>
  <rect x="725" y="438" width="150" height="182" fill="#f97316"/><text x="800" y="646" text-anchor="middle" class="body">13.14</text>
  <rect x="1220" y="540" width="150" height="80" fill="#0f766e"/><text x="1295" y="646" text-anchor="middle" class="body">12.18</text>

  <text x="305" y="690" text-anchor="middle" class="small">baseline MAE</text>
  <text x="800" y="690" text-anchor="middle" class="small">no semantic gain</text>
  <text x="1295" y="690" text-anchor="middle" class="small">workflow meaning helps</text>

  <rect x="360" y="792" width="880" height="78" rx="26" fill="#ecfdf5" stroke="#0f766e" stroke-width="3"/>
  <text x="800" y="826" text-anchor="middle" class="label">Conclusion: the improvement is not just extra parameter capacity.</text>
  <text x="800" y="856" text-anchor="middle" class="small">It requires the token to preserve the real video-to-workflow assignment.</text>
</svg>
SVG

for svg in "$svg1" "$svg2" "$svg3" "$svg4" "$svg5" "$svg6" "$svg7" "$svg8"; do
  render_one "$svg"
done

printf 'Generated natural concept figures in %s and mirrored to %s\n' "$OUT" "$SUB"
