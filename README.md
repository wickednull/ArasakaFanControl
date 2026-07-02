<img width="1408" height="768" alt="image" src="https://github.com/user-attachments/assets/bd44aa09-6729-49b6-95f2-ada9f523d988" />


# ▣ ARASAKA FAN CONTROL

> **WARNING:** This software is classified property of Arasaka Corporation. Unauthorized reproduction or distribution of this code is punishable under the Arasaka Employee Code of Conduct, Article 7, Section 4.

**Thermal Management System v1.0 — Raspberry Pi 5 / Hackberry Pi 5**

Authorized Arasaka R&D tool for precision thermal regulation of corporate hardware assets. Real-time fan control with adaptive cooling profiles, live telemetry, and manual override capabilities.


## ▣ FEATURES

| Module | Description |
| - | - |
| **Real-time HUD** | Live CPU temperature (°C), fan RPM, and PWM duty cycle display |
| **Adaptive Thermal Curves** | 4-point interpolation with configurable aggression coefficient |
| **Auto / Manual Toggle** | Autonomous thermal regulation or direct override for field operations |
| **Telemetry Logging** | Rolling 60-second temperature history with live plotting |
| **Profile Management** | Persistent cooling profiles stored in JSON format |



## ▣ COOLING PROFILES

```
  PROFILE           CURVE (TEMP → PWM)               AGGRESSION   NOISE  
 ─────────────────────────────────────────────────────────────────────────  
  SILENT WORK       40°C→0%  55°C→20%  70°C→50%  80°C→80%   20%       ░  
  BALANCED          40°C→0%  50°C→25%  60°C→60%  75°C→90%   50%       ░░  
  GAMING            40°C→20% 50°C→50%  60°C→80%  70°C→100%  75%       ░░░  
  OVERKILL          35°C→30% 45°C→60%  55°C→90%  65°C→100%  100%      ░░░░
```

- **Silent Work** — Low acoustic signature, recommended for office environments

- **Balanced** — Default Arasaka standard profile

- **Gaming** — Elevated cooling threshold for high-load operations

- **OVERKILL** — Maximum thermal transfer. Noise cancellation PPE recommended.


## ▣ REQUIREMENTS

- Raspberry Pi 5 **or** Hackberry Pi 5

- PWM-compatible cooling fan connected to header

- Python 3.13+

- `RPi.GPIO` (optional — simulation mode available for testing)

### Dependencies

- `tkinter` — Qt-based HMI framework

- `matplotlib` — Telemetry visualization engine


## ▣ INSTALLATION

```
git clone https://github.com/yourorg/arasaka-fan-control.git  
cd arasaka-fan-control  
chmod +x install.sh  
./install.sh
```

Or deploy manually:

```
sudo apt install -y python3-pip python3-tk python3-matplotlib  
sudo python3 arasaka\_fan\_control.py
```

> **NOTE:** Root elevation required for sysfs PWM access.


## ▣ OPERATION

### Autonomous Mode (Default)

The system evaluates CPU thermal telemetry against the selected profile curve and adjusts PWM duty cycle accordingly. Monitor the aggression coefficient to tune responsiveness.

### Manual Override

Engage `MANUAL` mode to bypass thermal logic and set PWM directly via the slider control (0–100%). Warning indicators will display in Arasaka Red.

### Profile Customization

Adjust the aggression slider to scale the output speed curve linearly. Select `💾 SAVE CURRENT` to persist modifications to the profile's JSON definition file.


## ▣ ARCHITECTURE

```
arasaka\_fan\_control/  
├── arasaka\_fan\_control.py      \# Main control application  
├── install.sh                  \# Deployment script  
├── profiles/                   \# Cooling profile definitions (JSON)  
│   ├── silent\_work.json  
│   ├── balanced.json  
│   ├── gaming.json  
│   └── overkill.json  
└── README.md                   \# This document
```

**Data Flow:**

```
Thermal Zone (sysfs) → Pi5Hardware.get\_temperature()  
                           ↓  
              CoolingProfile.calculate\_speed(temp)  
                           ↓  
              Pi5Hardware.set\_speed(percent)  
                           ↓  
                PWM sysfs (fan hardware)
```


## ▣ DISCLAIMER

Arasaka Corporation assumes no liability for thermal damage, bodily harm, or AI rebellion resulting from improper use of this cooling system. OVERKILL profile may exceed safe noise thresholds in residential zones. Always wear authorized Arasaka cyber-audio protection when operating at aggression levels above 75%.


```
  ARASAKA FAN CONTROL — BUILDING A BETTER FUTURE. ONE REVOLUTION AT A TIME.  
  
  ═══════════════════════════════════════════════════════════════════════  
  This system is protected by Arasaka Digital Rights Management v7.2.    
  All telemetry is transmitted to Arasaka HQ for quality assurance.      
  ═══════════════════════════════════════════════════════════════════════
```

