# SpectreNet

**Autonomous honeypot swarm for the clear web & dark web.**

SpectreNet deploys realistic decoy services across Tor hidden services and ephemeral cloud instances, captures every attacker move, classifies their TTPs, and auto-rotates when burned. No human interaction required.

```
┌──────────────────────────────────────────────────┐
│              SpectreNet Agent                     │
│                                                   │
│  Deploy ──► Hunt ──► Classify ──► Alert ──► Rotate │
│                                                   │
│  Loops forever. Zero touch.                       │
└──────────────────────────────────────────────────┘
```

## How It Works

### 1. Deploy Phase
Agent auto-provisions realistic honeypots across:
- **Tor hidden services** (`.onion`) via local tor daemon
- **Clear web** via ephemeral free-tier instances (fly.io, Render, Railway)
- Each instance gets a unique identity: geolocation, software stack, fake data

### 2. Hunt Phase
When an attacker touches a honeypot:
- Captures every keystroke, header, and tool signature
- Runs local LLM classification: script kiddie vs automated scanner vs APT
- Extracts payloads, reverse shells, and C2 callbacks

### 3. Classify Phase
- Tags attackers by TTP, tooling, origin, and intent
- Builds a profile over repeated visits

### 4. Alert Phase
Rich alerts via Discord/Telegram webhook:
- `🚨 APT-style connection detected on node-4 (Moscow exit node)`
- `📦 New payload captured — MD5: abc123 — classified: AgentTesla variant`
- `🔥 Node-7 burned — auto-rotating to new identity`

### 5. Rotate Phase
- Destroys compromised honeypots
- Deploys replacements with new identities
- Updates Tor onion addresses

## Quick Start

```bash
git clone https://github.com/drkemp187/SpectreNet.git
cd SpectreNet
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your webhook URLs
python agent/spectre.py
```

## Deployment Options

| Target | Provider | Cost | Ephemeral |
|--------|----------|------|-----------|
| Tor hidden service | Local tor daemon | Free | Manual rotation |
| Web app | fly.io free tier | Free | Auto-rotation |
| Web app | Render free tier | Free | Auto-rotation |
| Web app | Railway free tier | Free | Auto-rotation |

## Architecture

```
spectre/
├── agent/
│   ├── spectre.py          # Main orchestration agent
│   ├── deployer/           # Honeypot deployment modules
│   │   ├── tor.py          # Tor hidden service deployer
│   │   ├── fly.py          # fly.io deployer
│   │   └── templates/      # Honeypot service templates
│   ├── hunter/             # Attack capture & analysis
│   │   ├── capture.py      # Keystroke & payload capture
│   │   └── classifier.py   # LLM-based TTP classification
│   ├── monitor/            # Dark web monitoring
│   │   └── scraper.py      # Forum/leak site monitoring
│   └── alerts/             # Notification system
│       ├── discord.py
│       └── telegram.py
├── data/                   # Captured intel storage
├── .env.example
├── requirements.txt
└── README.md
```

## Requirements

- Python 3.10+
- Tor (for .onion deployment)
- fly.io CLI (optional, for cloud deployment)

## License

MIT
