# Using Claude in VS Code — BariatricRSD Project

> **Lambda instance (primary):** `192.222.50.14` — GH200 480GB, us-east-3 (runs Run 022 5-fold CV)
> **Lambda instance (secondary, causal-track):** `192.222.56.188` — GH200 96GB ARM64, us-east-3, `bariatric-rsd` filesystem attached (causal-cluster dev)
> **SSH key:** `/Users/bill/Documents/GitHub/bariatric_rsd/rsd.pem`
> **Project path:** `/home/ubuntu/bariatric-rsd`
> **Persistent storage:** `/lambda/nfs/bariatric-rsd/` (region-locked to us-east-3; attach to every new instance)

**Active experiments (as of 2026-04-24):**
- **Run 022** — MB140 5-fold CV, folds {1,2,3,4} × seeds {42,123,777}, screen `train022` on primary. ETA 2026-04-25 ~17:00 UTC.
- **Causal-cluster track** — `brsd_lib.causal_cluster` added. Smoke test waiting on secondary GH200 instance. See [SESSION_LOG.md](../../papers/paper1_neurips2026/notes/SESSION_LOG.md) Session 14 for the "retrospective → causal" pivot and rationale.

---

## Part 1 — Connect VS Code to Lambda

### Step 1 — Install Remote SSH extension

1. Press `Cmd+Shift+X` to open Extensions
2. Search **Remote - SSH**
3. Install the one by Microsoft
4. Restart VS Code if prompted

---

### Step 2 — Add Lambda to SSH config

Press `Cmd+Shift+P` → type **Remote-SSH: Open SSH Configuration File** → select `/Users/bill/.ssh/config`

Add this block:

```
Host lambda-rsd
    HostName 192.222.50.14
    User ubuntu
    IdentityFile /Users/bill/Documents/GitHub/bariatric_rsd/rsd.pem
    ServerAliveInterval 60
    ServerAliveCountMax 10
```

> **Every time you relaunch a Lambda instance the IP changes.**  
> Update `HostName` with the new IP from the Lambda dashboard.

---

### Step 3 — Fix key permissions (run once in Mac terminal)

```bash
chmod 400 /Users/bill/Documents/GitHub/bariatric_rsd/rsd.pem
```

---

### Step 4 — Connect

1. Press `Cmd+Shift+P`
2. Type **Remote-SSH: Connect to Host**
3. Select **lambda-rsd**
4. New VS Code window opens — select **Linux** when prompted
5. Wait ~30 seconds for VS Code server to install on the instance

---

### Step 5 — Open project folder

`File → Open Folder → /home/ubuntu/bariatric-rsd`

---

### Step 6 — Set Python interpreter

1. Press `Cmd+Shift+P`
2. Type **Python: Select Interpreter**
3. Select:

```
~/miniconda/envs/bariatric-rsd/bin/python
```

The status bar at the bottom left should show **bariatric-rsd**.

---

### Step 7 — Open integrated terminal

Press `` Ctrl+` `` then verify everything is working:

```bash
conda activate bariatric-rsd
nvidia-smi
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

You should see **NVIDIA GH200 480GB**.

---

## Part 2 — Install Claude in VS Code

### Option A — Claude.ai in browser (what you are doing now)

Keep `claude.ai` open alongside VS Code. Copy error messages or code in, get answers back. No setup needed.

Best for: questions, architecture decisions, writing paper sections.

---

### Option B — Continue.dev (free, Claude API directly in editor)

1. Press `Cmd+Shift+X` → search **Continue**
2. Install **Continue** by Continue
3. Click the Continue icon in the left sidebar
4. Click the settings gear → open `config.json`
5. Replace the contents with:

```json
{
  "models": [
    {
      "title": "Claude Sonnet",
      "provider": "anthropic",
      "model": "claude-sonnet-4-6",
      "apiKey": "YOUR_ANTHROPIC_API_KEY"
    }
  ]
}
```

6. Get your API key from `console.anthropic.com → API Keys`
7. Replace `YOUR_ANTHROPIC_API_KEY` with your actual key
8. Save — Claude is now available inline

| Shortcut | Action |
|---|---|
| `Cmd+L` | Open Claude chat panel |
| `Cmd+I` | Edit highlighted code inline with Claude |

---

### Option C — GitHub Copilot with Claude models

1. `Cmd+Shift+X` → search **GitHub Copilot**
2. Install **GitHub Copilot** and **GitHub Copilot Chat**
3. Sign in with GitHub account
4. In Copilot Chat, click the model selector → choose Claude Sonnet

> Requires GitHub Copilot subscription (~$10/month). Free trial may be available.

---

## Part 3 — Prompts for this project

Copy and paste these directly into Claude.

### When you get an error

```
I'm training BariatricRSD on a Lambda GH200 instance.
Here is the error I got:

[PASTE FULL ERROR TRACEBACK HERE]

The relevant code is in src/models/bariatric_rsd.py.
What is causing this and how do I fix it?
```

---

### When loss is not decreasing

```
My BariatricRSD training loss is not decreasing after 5 epochs.
Train loss: [PASTE VALUES]
Val MAE: [PASTE MAE]
Config: batch_size=32, lr=1e-4, sequence_len=8, embed_dim=768
What should I try first?
```

---

### When you want to understand a paper

```
Explain how Surgformer's Hierarchical Temporal Attention works
and how it differs from standard Transformer attention.
I am using it as the temporal backbone for RSD prediction in
laparoscopic bariatric surgery videos.
```

---

### When writing the paper

```
Write the Methods section paragraph describing the phase-order
token embedding in BariatricRSD. It is a learnable embedding
that encodes the surgeon's procedural style across 8 phase-order
clusters and is prepended to the Transformer input sequence.
Write in NeurIPS style, 150 words.
```

---

### When comparing results

```
My model gets MAE = X min on Cholec80.
TransLocal gets 7.1 min. BetaMixer gets F1=0.76 on MultiBypass140.
Write a 3-sentence Results paragraph comparing these numbers
for the NeurIPS 2026 paper.
```

---

### When you want to improve a specific function

```
Here is my current encode_frames function in bariatric_rsd.py:

[PASTE FUNCTION]

It is too slow during training. How can I speed it up
without changing the output tensor shape?
```

---

## Part 4 — Daily workflow

### Starting a session

```bash
# 1. Check Lambda dashboard for current IP
# 2. Update ~/.ssh/config if IP changed
# 3. Connect in VS Code: Cmd+Shift+P → Remote-SSH: Connect to Host → lambda-rsd
# 4. Open terminal: Ctrl+`

conda activate bariatric-rsd
nvidia-smi
screen -ls          # check what background sessions are running
```

---

### Starting training

```bash
cd /home/ubuntu/bariatric-rsd
conda activate bariatric-rsd

python src/training/train.py \
  --label_json labels/bariatric_labels.json \
  --data_root /home/ubuntu/bariatric-rsd/extern/MultiBypass140/datasets \
  --output_dir outputs/run_001 \
  --epochs 50 \
  --batch_size 32
```

---

### Running training in background (survives disconnection)

```bash
screen -S training
conda activate bariatric-rsd
python src/training/train.py [your args]

# Detach without stopping:  Ctrl+A then D
# Reattach later:           screen -r training
# List all sessions:        screen -ls
```

---

### Resuming from a checkpoint

```bash
python src/training/train.py \
  --resume outputs/run_001/best_model.pth \
  --label_json labels/bariatric_labels.json \
  --data_root /home/ubuntu/bariatric-rsd/extern/MultiBypass140/datasets \
  --output_dir outputs/run_001
```

---

### Monitoring training

```bash
# Watch GPU usage live
watch -n 2 nvidia-smi

# Tail training log
tail -f outputs/run_001/train.log

# Check download progress
screen -r download
```

WandB dashboard: `https://wandb.ai/your-username/bariatric-rsd-neurips2026`

---

### Before terminating the instance

> **Warning:** `/home/ubuntu/` is wiped when the instance terminates.  
> Only `/lambda/nfs/` persists. Always copy before stopping.

```bash
# Copy everything important to persistent filesystem
cp -r outputs/   /lambda/nfs/bariatric-rsd/outputs/
cp -r labels/    /lambda/nfs/bariatric-rsd/labels/
cp -r weights/   /lambda/nfs/bariatric-rsd/weights/

# Verify
ls /lambda/nfs/bariatric-rsd/
```

---

## Quick reference

| Action | Command / Shortcut |
|---|---|
| Connect to Lambda | `Cmd+Shift+P` → Remote-SSH: Connect to Host → lambda-rsd |
| Open project folder | `File → Open Folder → /home/ubuntu/bariatric-rsd` |
| Open terminal | `` Ctrl+` `` |
| Command palette | `Cmd+Shift+P` |
| Open Claude chat (Continue) | `Cmd+L` |
| Inline code edit with Claude | `Cmd+I` (highlight code first) |
| Activate conda env | `conda activate bariatric-rsd` |
| Check GPU | `nvidia-smi` |
| Start background session | `screen -S training` |
| Detach from screen | `Ctrl+A` then `D` |
| Reattach to screen | `screen -r training` |
| List screen sessions | `screen -ls` |
| Copy to persistent storage | `cp -r outputs/ /lambda/nfs/bariatric-rsd/outputs/` |
| SSH key | `/Users/bill/Documents/GitHub/bariatric_rsd/rsd.pem` |
| Instance IP | `192.222.50.14` (update when relaunched) |
| Persistent storage | `/lambda/nfs/bariatric-rsd/` |
| WandB project | `bariatric-rsd-neurips2026` |

---

## NeurIPS 2026 deadline

| Milestone | Date |
|---|---|
| Abstract due | May 4, 2026 AoE |
| Full paper due | **May 6, 2026 AoE** |
| Author notification | September 2026 |
| Conference | December 6–12, 2026 |
