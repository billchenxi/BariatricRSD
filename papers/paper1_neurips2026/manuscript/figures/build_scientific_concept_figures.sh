#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/paper/figures"
SUB="$ROOT/paper/Formatting_Instructions_For_NeurIPS_2026/figures"
FRAME_DIR="$ROOT/lambda_mirror/extern/MultiBypass140/datasets/MultiBypass140/BernBypass70/frames/BBP12"

mkdir -p "$OUT" "$SUB"

img() {
  base64 < "$FRAME_DIR/$1" | tr -d '\n'
}

F3439="$(img BBP12_00003439.jpg)"
F3444="$(img BBP12_00003444.jpg)"
F3449="$(img BBP12_00003449.jpg)"
F3454="$(img BBP12_00003454.jpg)"
F3459="$(img BBP12_00003459.jpg)"
F3464="$(img BBP12_00003464.jpg)"
F3469="$(img BBP12_00003469.jpg)"
F3474="$(img BBP12_00003474.jpg)"

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
      .title{font-family:Avenir Next,Arial,sans-serif;font-size:38px;font-weight:800;fill:#111827}
      .subtitle{font-family:Avenir Next,Arial,sans-serif;font-size:21px;font-weight:500;fill:#4b5563}
      .section{font-family:Avenir Next,Arial,sans-serif;font-size:24px;font-weight:800;fill:#111827}
      .label{font-family:Avenir Next,Arial,sans-serif;font-size:18px;font-weight:700;fill:#111827}
      .body{font-family:Avenir Next,Arial,sans-serif;font-size:17px;font-weight:500;fill:#374151}
      .small{font-family:Avenir Next,Arial,sans-serif;font-size:14px;font-weight:600;fill:#475569}
      .tiny{font-family:Avenir Next,Arial,sans-serif;font-size:12px;font-weight:700;fill:#64748b}
      .mono{font-family:Menlo,Consolas,monospace;font-size:15px;font-weight:600;fill:#111827}
      .monoSmall{font-family:Menlo,Consolas,monospace;font-size:12px;font-weight:600;fill:#334155}
      .card{fill:#ffffff;stroke:#d8dee8;stroke-width:2}
      .blue{fill:#eff6ff;stroke:#2563eb;stroke-width:2.5}
      .orange{fill:#fff7ed;stroke:#ea580c;stroke-width:2.5}
      .teal{fill:#ecfdf5;stroke:#0f766e;stroke-width:2.5}
      .purple{fill:#f5f3ff;stroke:#7c3aed;stroke-width:2.5}
      .red{fill:#fef2f2;stroke:#dc2626;stroke-width:2.5}
      .gray{fill:#f8fafc;stroke:#cbd5e1;stroke-width:2}
    </style>
    <filter id="shadow" x="-15%" y="-20%" width="130%" height="150%">
      <feDropShadow dx="0" dy="6" stdDeviation="7" flood-color="#0f172a" flood-opacity="0.10"/>
    </filter>
    <marker id="arrow" markerWidth="14" markerHeight="14" refX="12" refY="7" orient="auto">
      <path d="M0,0 L14,7 L0,14 Z" fill="#334155"/>
    </marker>
    <marker id="arrowBlue" markerWidth="14" markerHeight="14" refX="12" refY="7" orient="auto">
      <path d="M0,0 L14,7 L0,14 Z" fill="#2563eb"/>
    </marker>
    <marker id="arrowTeal" markerWidth="14" markerHeight="14" refX="12" refY="7" orient="auto">
      <path d="M0,0 L14,7 L0,14 Z" fill="#0f766e"/>
    </marker>
  </defs>
SVG
}

frame_card() {
  local x="$1" y="$2" w="$3" h="$4" img="$5" color="$6" lab="$7"
  cat <<SVG
  <clipPath id="clip_${x}_${y}"><rect x="$x" y="$y" width="$w" height="$h" rx="10"/></clipPath>
  <rect x="$x" y="$y" width="$w" height="$h" rx="10" fill="#fff" stroke="$color" stroke-width="4"/>
  <image x="$x" y="$y" width="$w" height="$h" href="data:image/jpeg;base64,$img" preserveAspectRatio="xMidYMid slice" clip-path="url(#clip_${x}_${y})"/>
  <rect x="$x" y="$y" width="$w" height="$h" rx="10" fill="none" stroke="$color" stroke-width="4"/>
  <text x="$((x + w / 2))" y="$((y + h + 22))" text-anchor="middle" class="tiny">$lab</text>
SVG
}

fig1="$OUT/fig_scientific01_clip_protocol_bbp12.svg"
cat > "$fig1" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
$(common_defs)
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="72" class="title">Concept 1: the clip protocol changes what evidence is visible</text>
  <text x="70" y="108" class="subtitle">Real MB140 example: BBP12 validation frames sampled every 5 s. Phase labels shown here are annotations, not inference inputs.</text>

  <rect x="72" y="155" width="1456" height="310" rx="26" class="card" filter="url(#shadow)"/>
  <text x="105" y="202" class="section">Strict prefix-only clip</text>
  <text x="105" y="232" class="body">The 8-frame clip ends at the prediction timestamp. Here the target would be t = 3474 s, RSD = 3010 s.</text>
  <line x1="215" y1="368" x2="1460" y2="368" stroke="#cbd5e1" stroke-width="3"/>
  $(frame_card 250 270 130 78 "$F3439" "#2563eb" "t-35")
  $(frame_card 400 270 130 78 "$F3444" "#2563eb" "t-30")
  $(frame_card 550 270 130 78 "$F3449" "#2563eb" "t-25")
  $(frame_card 700 270 130 78 "$F3454" "#2563eb" "t-20")
  $(frame_card 850 270 130 78 "$F3459" "#2563eb" "t-15")
  $(frame_card 1000 270 130 78 "$F3464" "#2563eb" "t-10")
  $(frame_card 1150 270 130 78 "$F3469" "#2563eb" "t-5")
  $(frame_card 1300 270 130 78 "$F3474" "#ea580c" "t")
  <rect x="535" y="415" width="460" height="34" rx="17" fill="#dbeafe"/>
  <text x="765" y="438" text-anchor="middle" class="small">visual frames are all at or before t</text>

  <rect x="72" y="515" width="1456" height="330" rx="26" class="card" filter="url(#shadow)"/>
  <text x="105" y="562" class="section">Centered-window clip</text>
  <text x="105" y="592" class="body">The same 8 sampled frames can be centered on t = 3459 s, RSD = 3025 s; three later frames are then visible.</text>
  <line x1="215" y1="726" x2="1460" y2="726" stroke="#cbd5e1" stroke-width="3"/>
  $(frame_card 250 628 130 78 "$F3439" "#2563eb" "t-20")
  $(frame_card 400 628 130 78 "$F3444" "#2563eb" "t-15")
  $(frame_card 550 628 130 78 "$F3449" "#2563eb" "t-10")
  $(frame_card 700 628 130 78 "$F3454" "#2563eb" "t-5")
  $(frame_card 850 628 130 78 "$F3459" "#ea580c" "t")
  $(frame_card 1000 628 130 78 "$F3464" "#dc2626" "t+5")
  $(frame_card 1150 628 130 78 "$F3469" "#dc2626" "t+10")
  $(frame_card 1300 628 130 78 "$F3474" "#dc2626" "t+15")
  <rect x="986" y="790" width="445" height="34" rx="17" fill="#fee2e2"/>
  <text x="1208" y="813" text-anchor="middle" class="small">post-target frames are inside the clip</text>
  <rect x="270" y="790" width="560" height="34" rx="17" fill="#e0f2fe"/>
  <text x="550" y="813" text-anchor="middle" class="small">BBP12 annotations near t: Omentum division -> Gastro-jejunal anastomosis</text>
</svg>
SVG

fig2="$OUT/fig_scientific02_causal_inference_soft_token.svg"
cat > "$fig2" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
$(common_defs)
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="72" class="title">Concept 2: causal-at-inference soft workflow token</text>
  <text x="70" y="108" class="subtitle">At inference the cluster signal is computed from model-predicted prefix phases, not from ground-truth labels or the full case.</text>

  <rect x="70" y="155" width="360" height="700" rx="26" class="card" filter="url(#shadow)"/>
  <text x="105" y="205" class="section">Observed pixels</text>
  <text x="105" y="236" class="body">One current clip, ending at t</text>
  <text x="105" y="262" class="mono">x_{t-35:t}, example t = 3474 s</text>
  $(frame_card 105 302 130 78 "$F3439" "#2563eb" "t-35")
  $(frame_card 255 302 130 78 "$F3444" "#2563eb" "t-30")
  $(frame_card 105 425 130 78 "$F3449" "#2563eb" "t-25")
  $(frame_card 255 425 130 78 "$F3454" "#2563eb" "t-20")
  $(frame_card 105 548 130 78 "$F3459" "#2563eb" "t-15")
  $(frame_card 255 548 130 78 "$F3464" "#2563eb" "t-10")
  $(frame_card 105 671 130 78 "$F3469" "#2563eb" "t-5")
  $(frame_card 255 671 130 78 "$F3474" "#ea580c" "t")
  <text x="250" y="820" text-anchor="middle" class="small">For the full prefix, repeat this over all clips up to t.</text>

  <path d="M450 335 C495 335, 515 290, 540 290" stroke="#334155" stroke-width="4" fill="none" marker-end="url(#arrow)"/>
  <rect x="555" y="165" width="380" height="250" rx="22" class="blue" filter="url(#shadow)"/>
  <text x="585" y="210" class="section">First pass</text>
  <text x="585" y="245" class="mono">ViT-B/16 -> frame features [8,768]</text>
  <text x="585" y="282" class="mono">placeholder z slot</text>
  <text x="585" y="319" class="mono">phase head -> p(phi | pixels)</text>
  <rect x="585" y="345" width="315" height="42" rx="16" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="742" y="372" text-anchor="middle" class="small">phase logits do not read workflow token</text>

  <path d="M745 425 L745 515" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="555" y="535" width="380" height="160" rx="22" class="card" filter="url(#shadow)"/>
  <text x="585" y="580" class="section">Predicted prefix sequence</text>
  <text x="585" y="616" class="mono">argmax p(phi) per clip</text>
  <text x="585" y="652" class="mono">phi_hat(x_{1:t}) = [2,2,2,3,...]</text>

  <path d="M955 615 L1065 615" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="1080" y="180" width="420" height="260" rx="22" class="purple" filter="url(#shadow)"/>
  <text x="1110" y="225" class="section">Fitted offline transform</text>
  <text x="1110" y="260" class="mono">TF-IDF bigram vector</text>
  <text x="1110" y="294" class="mono">PCA -> u</text>
  <text x="1110" y="328" class="mono">centroid distances d_k = ||u-c_k||^2</text>
  <text x="1110" y="362" class="mono">q_k = softmax(-d_k / tau)</text>
  <text x="1110" y="396" class="small">MB140: K=6, tau=0.01 in experiments</text>

  <path d="M1290 455 L1290 535" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="1050" y="555" width="480" height="165" rx="22" class="orange" filter="url(#shadow)"/>
  <text x="1080" y="602" class="section">Soft workflow token</text>
  <text x="1080" y="640" class="mono">e_z = sum_k q_k E[k,:]</text>
  <text x="1080" y="672" class="body">Replace placeholder token, then</text>
  <text x="1080" y="700" class="body">re-run temporal/RSD head.</text>

  <path d="M1050 700 C1000 755, 980 782, 950 782" stroke="#0f766e" stroke-width="5" fill="none" marker-end="url(#arrowTeal)"/>
  <rect x="560" y="735" width="390" height="95" rx="22" class="teal" filter="url(#shadow)"/>
  <text x="755" y="774" text-anchor="middle" class="section">Final prediction</text>
  <text x="755" y="808" text-anchor="middle" class="mono">RSD head -> y_hat_t</text>

  <rect x="1010" y="785" width="500" height="58" rx="18" class="red"/>
  <text x="1260" y="809" text-anchor="middle" class="label">Forbidden at inference</text>
  <text x="1260" y="834" text-anchor="middle" class="small">GT phase labels, full-video phase sequence, full-video cluster z</text>
</svg>
SVG

fig3="$OUT/fig_scientific03_offline_workflow_cluster.svg"
cat > "$fig3" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
SVG
common_defs >> "$fig3"
cat >> "$fig3" <<'SVG'
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="72" class="title">Concept 3: what the workflow cluster actually encodes</text>
  <text x="70" y="108" class="subtitle">The token is a learned embedding for a phase-order cluster, not a duration bin and not the raw phase labels.</text>

  <rect x="70" y="155" width="1460" height="675" rx="28" class="card" filter="url(#shadow)"/>
  <text x="105" y="205" class="section">Offline fitting, using training-set phase annotations</text>
  <text x="105" y="236" class="body">Example from MB140 BBP12: full compressed phase sequence, cluster z = 1.</text>

  <rect x="105" y="290" width="310" height="250" rx="20" class="blue"/>
  <text x="130" y="330" class="label">1. Full phase sequence</text>
  <text x="130" y="370" class="monoSmall">Preparation</text>
  <text x="130" y="398" class="monoSmall">Gastric pouch creation</text>
  <text x="130" y="426" class="monoSmall">Omentum division</text>
  <text x="130" y="454" class="monoSmall">Gastro-jejunal anastomosis</text>
  <text x="130" y="482" class="monoSmall">Jejuno-jejunal anastomosis</text>
  <text x="130" y="510" class="monoSmall">Jejunal div. -> Leak -> Cleaning</text>

  <path d="M435 415 L520 415" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="540" y="290" width="300" height="250" rx="20" class="teal"/>
  <text x="565" y="330" class="label">2. Transition bigrams</text>
  <text x="565" y="370" class="monoSmall">prep -> pouch</text>
  <text x="565" y="398" class="monoSmall">pouch -> omentum</text>
  <text x="565" y="426" class="monoSmall">omentum -> GJ</text>
  <text x="565" y="454" class="monoSmall">GJ -> JJ</text>
  <text x="565" y="482" class="monoSmall">JJ -> jejunal division</text>
  <text x="565" y="510" class="monoSmall">...</text>

  <path d="M860 415 L945 415" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="965" y="290" width="250" height="250" rx="20" class="purple"/>
  <text x="990" y="330" class="label">3. Vector space</text>
  <text x="990" y="370" class="monoSmall">TF-IDF over bigrams</text>
  <text x="990" y="408" class="monoSmall">PCA: 16 components</text>
  <text x="990" y="446" class="monoSmall">point u in PCA space</text>

  <path d="M1235 415 L1320 415" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="1340" y="290" width="150" height="250" rx="20" class="orange"/>
  <text x="1415" y="330" text-anchor="middle" class="label">4. k-means</text>
  <circle cx="1415" cy="405" r="44" fill="#fed7aa" stroke="#ea580c" stroke-width="4"/>
  <text x="1415" y="413" text-anchor="middle" class="label">z=1</text>
  <text x="1415" y="480" text-anchor="middle" class="small">MB140 K=6</text>

  <rect x="130" y="610" width="585" height="120" rx="22" class="gray"/>
  <text x="160" y="650" class="label">Oracle workflow token</text>
  <text x="160" y="686" class="mono">hard lookup: e_z = E[z,:]</text>
  <text x="160" y="716" class="small">Uses the full-video cluster label; diagnostic upper bound, not live inference.</text>

  <rect x="885" y="610" width="585" height="120" rx="22" class="gray"/>
  <text x="915" y="650" class="label">Causal-at-inference token</text>
  <text x="915" y="686" class="mono">soft mixture: e_z = sum_k q_k E[k,:]</text>
  <text x="915" y="716" class="small">Uses the same fitted transform, but applied to predicted prefix phases.</text>
</svg>
SVG

fig4="$OUT/fig_scientific04_oracle_dependency_scope.svg"
cat > "$fig4" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
SVG
common_defs >> "$fig4"
cat >> "$fig4" <<'SVG'
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="72" class="title">Concept 4: which oracle dependency is closed?</text>
  <text x="70" y="108" class="subtitle">The paper closes the inference-time cluster oracle. Training still uses privileged phase supervision for the prefix-derived cluster ID.</text>

  <rect x="75" y="170" width="450" height="600" rx="28" class="card" filter="url(#shadow)"/>
  <text x="300" y="225" text-anchor="middle" class="section">Retrospective oracle</text>
  <rect x="125" y="270" width="350" height="72" rx="18" class="red"/>
  <text x="300" y="300" text-anchor="middle" class="label">source of z</text>
  <text x="300" y="326" text-anchor="middle" class="small">full-video GT phase sequence</text>
  <path d="M300 355 L300 420" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="125" y="435" width="350" height="78" rx="18" class="orange"/>
  <text x="300" y="466" text-anchor="middle" class="mono">z = argmax centroid</text>
  <text x="300" y="493" text-anchor="middle" class="small">hard cluster ID</text>
  <rect x="125" y="580" width="350" height="82" rx="18" class="gray"/>
  <text x="300" y="613" text-anchor="middle" class="label">scope</text>
  <text x="300" y="641" text-anchor="middle" class="small">diagnostic upper bound; not deployable</text>

  <rect x="575" y="170" width="450" height="600" rx="28" class="card" filter="url(#shadow)"/>
  <text x="800" y="225" text-anchor="middle" class="section">Causal variant: training</text>
  <rect x="625" y="270" width="350" height="72" rx="18" class="red"/>
  <text x="800" y="300" text-anchor="middle" class="label">teacher-forced source</text>
  <text x="800" y="326" text-anchor="middle" class="small">GT phase prefix [0, t_mid]</text>
  <path d="M800 355 L800 420" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="625" y="435" width="350" height="78" rx="18" class="orange"/>
  <text x="800" y="466" text-anchor="middle" class="mono">hard prefix-derived z</text>
  <text x="800" y="493" text-anchor="middle" class="small">fallback if &lt;2 unique phases (~7%)</text>
  <rect x="625" y="580" width="350" height="82" rx="18" class="gray"/>
  <text x="800" y="613" text-anchor="middle" class="label">scope</text>
  <text x="800" y="641" text-anchor="middle" class="small">privileged training signal remains</text>

  <rect x="1075" y="170" width="450" height="600" rx="28" class="card" filter="url(#shadow)"/>
  <text x="1300" y="225" text-anchor="middle" class="section">Causal variant: inference</text>
  <rect x="1125" y="270" width="350" height="72" rx="18" class="teal"/>
  <text x="1300" y="300" text-anchor="middle" class="label">source of q</text>
  <text x="1300" y="326" text-anchor="middle" class="small">model-predicted phase prefix from pixels</text>
  <path d="M1300 355 L1300 420" stroke="#334155" stroke-width="4" marker-end="url(#arrow)"/>
  <rect x="1125" y="435" width="350" height="78" rx="18" class="purple"/>
  <text x="1300" y="466" text-anchor="middle" class="mono">q_k = softmax(-d_k / tau)</text>
  <text x="1300" y="493" text-anchor="middle" class="small">soft cluster posterior</text>
  <rect x="1125" y="580" width="350" height="82" rx="18" class="teal"/>
  <text x="1300" y="613" text-anchor="middle" class="label">scope</text>
  <text x="1300" y="641" text-anchor="middle" class="small">no GT phase labels; no full-case z</text>

  <rect x="290" y="815" width="1020" height="58" rx="18" fill="#fff7ed" stroke="#ea580c" stroke-width="2"/>
  <text x="800" y="851" text-anchor="middle" class="label">Correct wording: causal-at-inference, not fully causal training.</text>
</svg>
SVG

fig5="$OUT/fig_scientific05_results_scope_and_control.svg"
cat > "$fig5" <<'SVG'
<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="950" viewBox="0 0 1600 950">
SVG
common_defs >> "$fig5"
cat >> "$fig5" <<'SVG'
  <rect width="1600" height="950" fill="#f8fafc"/>
  <text x="70" y="72" class="title">Concept 5: the claim is a pattern across regimes, not one number</text>
  <text x="70" y="108" class="subtitle">Strict-protocol numbers support the deployment-relevant workflow-conditioning claim; controls test whether the token carries semantic information.</text>

  <rect x="75" y="165" width="690" height="310" rx="26" class="card" filter="url(#shadow)"/>
  <text x="110" y="215" class="section">MB140 within-center, strict prefix-only</text>
  <text x="110" y="250" class="body">Fold 0, 3 seeds; decoupled-oracle is the headline strict result.</text>
  <line x1="145" y1="400" x2="690" y2="400" stroke="#cbd5e1" stroke-width="3"/>
  <rect x="210" y="285" width="110" height="115" fill="#94a3b8"/><text x="265" y="430" text-anchor="middle" class="label">13.03</text><text x="265" y="455" text-anchor="middle" class="small">no token</text>
  <rect x="405" y="292" width="110" height="108" fill="#60a5fa"/><text x="460" y="430" text-anchor="middle" class="label">12.26</text><text x="460" y="455" text-anchor="middle" class="small">oracle</text>
  <rect x="600" y="300" width="110" height="100" fill="#0f766e"/><text x="655" y="430" text-anchor="middle" class="label">12.18</text><text x="655" y="455" text-anchor="middle" class="small">decoupled</text>
  <rect x="110" y="290" width="72" height="55" rx="14" class="teal"/>
  <text x="146" y="314" text-anchor="middle" class="label">-0.85</text>
  <text x="146" y="337" text-anchor="middle" class="tiny">min</text>

  <rect x="835" y="165" width="690" height="310" rx="26" class="card" filter="url(#shadow)"/>
  <text x="870" y="215" class="section">MB140 cross-center, strict prefix-only</text>
  <text x="870" y="250" class="body">Train Bern, validate Strasbourg, 3 seeds.</text>
  <line x1="905" y1="400" x2="1450" y2="400" stroke="#cbd5e1" stroke-width="3"/>
  <rect x="970" y="285" width="110" height="115" fill="#94a3b8"/><text x="1025" y="430" text-anchor="middle" class="label">17.80</text><text x="1025" y="455" text-anchor="middle" class="small">no token</text>
  <rect x="1165" y="292" width="110" height="108" fill="#60a5fa"/><text x="1220" y="430" text-anchor="middle" class="label">17.71</text><text x="1220" y="455" text-anchor="middle" class="small">oracle</text>
  <rect x="1360" y="315" width="110" height="85" fill="#0f766e"/><text x="1415" y="430" text-anchor="middle" class="label">17.33</text><text x="1415" y="455" text-anchor="middle" class="small">decoupled</text>
  <rect x="870" y="290" width="72" height="55" rx="14" class="teal"/>
  <text x="906" y="314" text-anchor="middle" class="label">-0.47</text>
  <text x="906" y="337" text-anchor="middle" class="tiny">min</text>

  <rect x="75" y="535" width="690" height="270" rx="26" class="card" filter="url(#shadow)"/>
  <text x="110" y="585" class="section">Cholec80 contrast case</text>
  <text x="110" y="620" class="body">Strict single-seed range is 0.08 min: no meaningful workflow-conditioning effect.</text>
  <rect x="130" y="665" width="160" height="70" rx="18" class="gray"/><text x="210" y="693" text-anchor="middle" class="label">4.34</text><text x="210" y="718" text-anchor="middle" class="small">no token</text>
  <rect x="330" y="665" width="160" height="70" rx="18" class="gray"/><text x="410" y="693" text-anchor="middle" class="label">4.33</text><text x="410" y="718" text-anchor="middle" class="small">oracle</text>
  <rect x="530" y="665" width="160" height="70" rx="18" class="gray"/><text x="610" y="693" text-anchor="middle" class="label">4.26</text><text x="610" y="718" text-anchor="middle" class="small">prefix</text>
  <text x="110" y="770" class="small">Centered-window teacher-forced prefix was worse (5.03 vs 4.61).</text>
  <text x="110" y="792" class="small">That negative effect does not reproduce under the strict protocol.</text>

  <rect x="835" y="535" width="690" height="270" rx="26" class="card" filter="url(#shadow)"/>
  <text x="870" y="585" class="section">Shuffled-token semantic control</text>
  <text x="870" y="620" class="body">If any extra vector helped, shuffled tokens should help. They do not.</text>
  <line x1="900" y1="735" x2="1465" y2="735" stroke="#cbd5e1" stroke-width="3"/>
  <rect x="955" y="635" width="105" height="100" fill="#94a3b8"/><text x="1007" y="765" text-anchor="middle" class="label">13.03</text><text x="1007" y="790" text-anchor="middle" class="small">no token</text>
  <rect x="1165" y="625" width="105" height="110" fill="#f97316"/><text x="1217" y="765" text-anchor="middle" class="label">13.14</text><text x="1217" y="790" text-anchor="middle" class="small">shuffled</text>
  <rect x="1375" y="680" width="105" height="55" fill="#0f766e"/><text x="1427" y="765" text-anchor="middle" class="label">12.18</text><text x="1427" y="790" text-anchor="middle" class="small">real token</text>
</svg>
SVG

for svg in "$fig1" "$fig2" "$fig3" "$fig4" "$fig5"; do
  render_one "$svg"
done

printf 'Generated scientific concept figures in %s and mirrored to %s\n' "$OUT" "$SUB"
