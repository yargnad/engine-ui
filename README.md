# Anima Locus Audio Engine & UI

**AGPLv3 Licensed** | Audio Processing + WebSocket API + Web Interface

Linux-side audio engines, sensor fusion, and Conductor UI for Anima Locus.

---

## Overview

This repository contains:

- **Audio engines** (granular, spectral, sampler)
- **Sensor fusion services** (radar + E-field + ToF → gesture recognition)
- **WebSocket + REST API** (OpenAPI spec)
- **Conductor UI** (web-based HUD with beat/dynamics meters, macros, XY pad)

### Architecture

```
┌─────────────────────────────────────────────────┐
│  Conductor UI (Web Browser / Embedded Display)  │
│  - Beat/Dynamics Meters   - Macros              │
│  - XY Pad                 - Scene Selector      │
└─────────────────┬───────────────────────────────┘
                  │ WebSocket + REST
┌─────────────────▼───────────────────────────────┐
│             API Server (FastAPI)                │
│  - Real-time control (WebSocket)                │
│  - Preset/scene management (REST)               │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           Sensor Fusion Layer                   │
│  - MCU link protocol parser                     │
│  - Gesture recognition (ML models)              │
│  - Environmental hysteresis                     │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│           Audio Engine Core                     │
│  - Granular synthesis                           │
│  - Spectral processing                          │
│  - Multi-sampler                                │
│  - Effects pipeline                             │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│         Audio I/O (JACK / PipeWire)             │
└─────────────────────────────────────────────────┘
```

---

## Audio Engines

### 1. Granular Engine

**Sensor Mappings:**
- **mmWave position:** Grain position in sample
- **E-field XYZ:** Grain size, density, pitch scatter
- **Environmental (humidity/CO₂):** Filter cutoff, resonance

**Parameters:**
- Grain size: 10-500 ms
- Density: 1-100 grains/sec
- Pitch scatter: ±2 octaves
- Sample position: 0-100%

### 2. Spectral Engine

**Sensor Mappings:**
- **Radar velocity:** Spectral freeze amount
- **ToF depth:** Frequency bin masking
- **Thermal gradient:** Partials emphasis

**Parameters:**
- FFT size: 4096-16384
- Overlap: 50-95%
- Bin masking: Frequency-selective attenuation
- Freeze: Hold spectral frame

### 3. Multi-Sampler

**Sensor Mappings:**
- **Gesture (ML):** Trigger samples
- **E-field approach:** Volume envelope
- **Environmental:** Filter/FX modulation

**Parameters:**
- Polyphony: 16 voices
- Trigger modes: One-shot, loop, gated
- ADSR per voice

### Effects Pipeline

- **Reverb:** Shimmer, plate, chamber
- **Delay:** Tape emulation, ping-pong
- **Distortion:** Waveshaper, bit crush
- **Filters:** SVF, comb, formant

---

## Sensor Fusion

### MCU Link Protocol

Consumes binary frames from STM32 firmware over UART/CDC:

```python
from anima_locus.link import LinkParser

parser = LinkParser('/dev/ttyACM0')
for message in parser.stream():
    if message.type == MessageType.SENSOR_SNAPSHOT:
        temp, humidity, co2 = message.environmental
        # Map to audio parameters...
    elif message.type == MessageType.GESTURE:
        gesture_id = message.gesture.class_id
        confidence = message.gesture.confidence
        # Trigger audio event...
```

### Gesture Recognition

**ML Pipeline:**
- MCU provides compact features (tinyML output)
- Linux runs larger models (ONNX/TFLite):
  - Temporal gesture classifier (LSTM/Transformer)
  - Conductor pattern recognition
  - Anomaly detection

**Gesture Library:**
- Swipe (left/right/up/down)
- Hold
- Tap
- Circle
- Push/pull
- Custom patterns (trainable)

### Hysteretic Mapping

Environmental sensors use hysteresis to prevent jitter:

```python
class HystereticMapper:
    def __init__(self, low, high, dead_zone=0.05):
        self.low = low
        self.high = high
        self.dead_zone = dead_zone
        self.state = None
```

Smooths slow-changing values (temperature, humidity, CO₂) over 10-60 second windows.

---

## API

### WebSocket (Real-Time Control)

**Endpoint:** `ws://[host]:8080/ws`

**Client → Server:**
```json
{
  "type": "set_param",
  "engine": "granular",
  "param": "grain_size",
  "value": 0.15
}
```

**Server → Client (Telemetry):**
```json
{
  "type": "telemetry",
  "sensors": {
    "temperature": 22.5,
    "humidity": 45.2,
    "co2": 412,
    "radar": {"x": 0.3, "y": -0.1, "z": 0.8}
  },
  "audio": {
    "cpu": 23.4,
    "xruns": 0
  }
}
```

### REST (Presets & Scenes)

**Base URL:** `http://[host]:8080/api/v1`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/presets` | GET | List all presets |
| `/presets/{id}` | GET | Get preset details |
| `/presets` | POST | Create new preset |
| `/presets/{id}` | PUT | Update preset |
| `/presets/{id}` | DELETE | Delete preset |
| `/scenes` | GET | List scenes |
| `/scenes/{id}` | GET | Load scene |

**Example Preset:**
```json
{
  "id": "preset-001",
  "name": "Ethereal Clouds",
  "engines": {
    "granular": {
      "enabled": true,
      "sample": "strings.wav",
      "grain_size": 0.25,
      "density": 30
    },
    "effects": {
      "reverb": {"decay": 4.5, "mix": 0.6},
      "delay": {"time": 0.375, "feedback": 0.4}
    }
  },
  "mappings": {
    "radar.x": "granular.position",
    "efield.y": "granular.density"
  }
}
```

---

## Conductor UI

### HUD Elements

**Left Column:**
- **Beat Meter** - Visual pulse sync (BPM-aware)
- **Dynamics Meter** - Audio level + sensor intensity blend

**Center:**
- **XY Pad** - Direct parameter control (radar position overlay)

**Right Column:**
- **Macros** - 8 assignable knobs
- **Scene Selector** - Preset browser

### Deployment

**Embedded (Arduino UNO Q):**
- Served locally via Uvicorn
- Access via `http://[device-ip]:8080`

**Remote:**
- Connect from any device on network
- WebSocket auto-reconnect on network changes

---

## Build & Run

### Prerequisites

- **Python:** 3.11+
- **Audio System:** JACK2 or PipeWire
- **Dependencies:** See `requirements.txt`

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server (development)
uvicorn anima_locus.server:app --reload --host 0.0.0.0 --port 8080

# Run server (production)
gunicorn -k uvicorn.workers.UvicornWorker anima_locus.server:app
```

### Docker Deployment

```bash
docker build -t anima-locus-engine .
docker run -d \
  --device /dev/ttyACM0 \
  --device /dev/snd \
  -p 8080:8080 \
  anima-locus-engine
```

---

## Directory Structure

```
engine-ui/
├── anima_locus/
│   ├── __init__.py
│   ├── server.py          # FastAPI app
│   ├── engines/           # Audio engines
│   │   ├── granular.py
│   │   ├── spectral.py
│   │   └── sampler.py
│   ├── fusion/            # Sensor fusion
│   │   ├── link.py        # MCU protocol parser
│   │   ├── gesture.py     # ML gesture recognition
│   │   └── hysteresis.py
│   ├── api/               # API routes
│   │   ├── websocket.py
│   │   └── rest.py
│   └── audio_io/          # JACK/PipeWire interface
├── ui/                    # Web UI (React/Svelte)
│   ├── src/
│   │   ├── components/
│   │   ├── stores/
│   │   └── main.js
│   └── dist/              # Built UI (served by FastAPI)
├── tests/
│   ├── test_engines.py
│   ├── test_api.py
│   └── test_fusion.py
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Testing

### Unit Tests

```bash
pytest tests/ -v
```

### API Contract Tests

```bash
# Validate OpenAPI spec
python -m anima_locus.api.validate

# Run integration tests
pytest tests/integration/ --api-url http://localhost:8080
```

### Audio Pipeline Tests

```bash
# Latency measurement
python -m anima_locus.tools.measure_latency

# CPU usage profiling
python -m anima_locus.tools.profile --duration 60
```

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Audio latency | < 10 ms | JACK at 48 kHz, 256 samples |
| CPU usage | < 40% | On NXP i.MX 93 (Cortex-A55) |
| WebSocket latency | < 5 ms | Local network |
| Telemetry rate | 30 Hz | Sensor updates |

---

## Licensing

Licensed under **GNU Affero General Public License v3.0** (AGPLv3).

See [LICENSE](./LICENSE) for full text.

### Third-Party Audio Libraries

- **NumPy:** BSD-3-Clause
- **SciPy:** BSD-3-Clause
- **librosa:** ISC License
- **sounddevice:** MIT License
- **FastAPI:** MIT License

All third-party components are compatible with AGPLv3.

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for:

- Coding standards
- Audio engine architecture guidelines
- API versioning policy
- Testing requirements

---

## Related Repositories

- [mcu-stm32/](../mcu-stm32/) - STM32 firmware (sensor scanning)
- [sdk-py/](../sdk-py/) - Python SDK (API client)
- [sdk-ts/](../sdk-ts/) - TypeScript SDK (Web integration)
- [docs-site/](../docs-site/) - Full documentation

---

## Links

- **FastAPI:** https://fastapi.tiangolo.com/
- **JACK Audio:** https://jackaudio.org/
- **PipeWire:** https://pipewire.org/

---

*Part of the [Anima Locus](../) project and [The Authentic Rebellion Framework](https://rebellion.musubiaccord.org) ecosystem.*
