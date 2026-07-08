# Contributing to SpectreNet

## Ideas for contributions

- Add more honeypot templates (WordPress, Jenkins, GitLab, etc.)
- Support more ephemeral providers (Railway, Render, Heroku)
- Improve LLM-based attacker classification
- Add PCAP logging for network-level capture
- Build a web dashboard for live attacker map
- Integrate with MISP/TheHive for threat intel sharing

## Quick start

```bash
git clone https://github.com/drkemp187/SpectreNet.git
cd SpectreNet
pip install -r requirements.txt
cp .env.example .env
# configure your webhooks
python agent/spectre.py
```
