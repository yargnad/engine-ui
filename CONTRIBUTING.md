# Contributing to Anima Locus Audio Engine & UI

See the main [Contributing Guide](../CONTRIBUTING.md) for general guidelines.

---

## Engine/UI-Specific Requirements

**License:** AGPLv3 (network copyleft)

### Code Style

**Python:**
- Python 3.11+ with type hints
- Black formatter (line length 100)
- isort for imports
- mypy strict mode

```bash
# Format code
black anima_locus/
isort anima_locus/

# Type check
mypy anima_locus/

# Lint
ruff check anima_locus/
```

**TypeScript (UI):**
- TypeScript strict mode
- ESLint (Airbnb config)
- Prettier formatting

```bash
npm run format
npm run lint
npm run typecheck
```

### Architecture Guidelines

**Audio Engines:**
- No blocking I/O in audio callback
- Pre-allocate buffers (no malloc in hot path)
- Target < 10 ms latency
- CPU usage < 40% on NXP i.MX 93

**API Server:**
- Async-first (FastAPI + uvicorn)
- WebSocket for real-time control
- REST for CRUD operations
- OpenAPI spec must stay in sync

**Sensor Fusion:**
- Hysteretic mapping for slow sensors
- ML models use ONNX or TFLite
- No blocking on MCU serial reads

### Testing

**Unit Tests:**
```bash
pytest tests/ -v --cov=anima_locus
```

**API Contract Tests:**
```bash
# Validate OpenAPI spec
python -m anima_locus.api.validate

# Integration tests
pytest tests/integration/ --api-url http://localhost:8080
```

**Audio Pipeline Tests:**
```bash
# Latency measurement
python -m anima_locus.tools.measure_latency

# CPU profiling
python -m anima_locus.tools.profile --duration 60
```

### Performance Requirements

| Metric | Target | Verification |
|--------|--------|--------------|
| Audio latency | < 10 ms | JACK tooling |
| CPU usage | < 40% | htop, perf |
| WebSocket latency | < 5 ms | Network analyzer |
| Telemetry rate | 30 Hz | Wireshark |

### Pull Request Checklist

- [ ] Code formatted (black, isort)
- [ ] Type hints for all public APIs
- [ ] Docstrings (Google style)
- [ ] Tests pass (pytest)
- [ ] Type check passes (mypy strict)
- [ ] API spec updated (if API changed)
- [ ] Performance requirements met
- [ ] DCO sign-off

### Commit Message Format

```
[engine] Add granular synthesis engine

Implements real-time granular synthesis with sensor control:
- Grain size, density, pitch scatter parameters
- Maps mmWave position to grain position
- Maps E-field to density and scatter

Tested with 256-sample buffer @ 48 kHz:
- Latency: 8.3 ms
- CPU: 32%

Fixes #37

Signed-off-by: Your Name <your.email@example.com>
```

### API Versioning

- **Backward-compatible changes:** Increment minor version (v1.2 → v1.3)
- **Breaking changes:** Increment major version (v1.x → v2.0)
- Document changes in `CHANGELOG.md`

### Debugging

**Audio Issues:**
```bash
# Check JACK status
jack_lsp -c

# Measure latency
jack_delay

# CPU usage
jack_cpu_load
```

**API Issues:**
```bash
# WebSocket debugging
websocat ws://localhost:8080/ws

# REST debugging
curl -X GET http://localhost:8080/api/v1/presets
```

---

## DCO Sign-Off

All commits must include:

```
Signed-off-by: Your Name <your.email@example.com>
```

Use `git commit -s` to add automatically.

---

## Questions?

Open a GitHub Discussion or see [main Contributing Guide](../CONTRIBUTING.md).

---

*Licensed under AGPLv3. See [LICENSE](./LICENSE).*
