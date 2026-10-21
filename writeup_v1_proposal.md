# NFL Big Data Bowl 2027: From Combine Movement to NFL Success

> **Competition theme:** *"Uncover non-obvious linkages between Combine sensor tracking and regular-season NFL game performance."*

## Executive Summary

The NFL Big Data Bowl 2027 challenges participants to discover meaningful relationships between player movement data collected during the NFL Scouting Combine and subsequent NFL regular season performance. Unlike traditional scouting methods that focus primarily on stopwatch times and standard athletic measurements, this competition provides access to high-frequency sensor tracking data that captures the complete movement profile of prospects during Combine drills. The objective is to uncover actionable insights that can help coaches, scouts, and front offices identify talent more effectively and make better draft decisions.

This write-up proposes an analytical framework centred on the concept of **Movement Efficiency Index (MEI)**, a composite metric designed to evaluate how effectively athletes translate athletic movement patterns demonstrated at the Combine into productive NFL performance.

```
 ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
 │  COMBINE SENSOR  │    │     FEATURE      │    │    MOVEMENT      │    │   NFL REGULAR    │
 │  TRACKING DATA   │───►│   ENGINEERING    │───►│   EFFICIENCY     │───►│ SEASON OUTCOMES  │
 │  (10 Hz x, y,    │    │ accel · decel ·  │    │   INDEX (MEI)    │    │ separation · EPA │
 │  speed, accel,   │    │ COD · smoothness │    │ position-        │    │ pressure · grade │
 │  direction)      │    │ · recovery       │    │ standardised     │    │                  │
 └──────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
                                                                                  │
                         ┌────────────────────────────────────────────────────────┘
                         ▼
               ┌────────────────────┐
               │ FOOTBALL OPS IMPACT│  draft · development · injury · contracts
               └────────────────────┘
```

---

## 1. Introduction

The NFL Scouting Combine has long served as the primary evaluation event for NFL prospects. Traditional metrics such as:

- 40-yard dash time
- Three-cone drill
- Short shuttle
- Vertical jump
- Broad jump

have historically been used to assess athletic ability. However, these single-number measures fail to capture the complexities of human movement. Modern tracking sensors record athlete location, speed, acceleration, and directional changes at a frequency of **10 Hz**, providing a much richer representation of player athleticism.

```
 Traditional measurement (one number)          Tracking measurement (10 samples / second)

   START ─────────────────────────► FINISH       START ●─●─●─●─●─●─●─●─●─●─●─●─●─●─● FINISH
                 4.45 s                                 │ │ │ │ │ │ │ │ │ │ │ │ │ │ │
                                                        x, y, speed, accel, direction
                                                        at every 0.1 s frame
```

The central question of the 2027 Big Data Bowl is:

> **Which movement characteristics observed during Combine drills are the strongest predictors of future NFL performance?**

## 2. Research Objective

The objective of this analysis is to develop a predictive framework linking Combine movement biomechanics with key NFL performance outcomes.

Specifically, this study seeks to determine:

1. Which movement traits best predict NFL success.
2. Whether tracking-based metrics outperform traditional Combine metrics.
3. Whether different position groups exhibit unique predictive movement signatures.
4. How scouting departments can use tracking data to identify undervalued prospects.

## 3. Hypothesis

Traditional Combine metrics measure **outcomes**, while tracking data measures **processes**.

For example:

| Traditional Metric | Tracking-Based Enhancement |
|---|---|
| 40-yard Dash Time | Acceleration curve, stride efficiency |
| Shuttle Time | Deceleration and re-acceleration efficiency |
| Three-Cone Time | Angular velocity and turning efficiency |
| Vertical Jump | Force generation profile |
| Position Drills | Movement smoothness and control |

We hypothesize that:

> **Tracking-derived movement efficiency metrics will demonstrate stronger relationships with NFL performance than traditional Combine measurements alone.**

## 4. Proposed Metric: Movement Efficiency Index (MEI)

To evaluate player movement comprehensively, we propose the Movement Efficiency Index.

### Components

#### 4.1 Acceleration Efficiency

Measures how rapidly a player reaches top speed.

```
Acceleration Efficiency = Peak Speed / Time to Peak Speed
```

Higher values indicate explosive athletes.

```
 speed
   ▲
   │          Player A (explosive)
   │        ╭──────────────────────────
   │      ╭─╯           ╭──────────────  Player B
   │     ╱          ╭───╯
   │    ╱       ╭───╯
   │   ╱    ╭───╯        Same peak speed, but A reaches it sooner
   │  ╱ ╭───╯            → higher Acceleration Efficiency
   │ ╱╭─╯
   └┴──┴──────┴──────────────────────────► time
       tA     tB
```

#### 4.2 Deceleration Control

Measures the ability to slow down under control.

Particularly important for:

- Wide Receivers
- Tight Ends
- Defensive Backs

```
Deceleration Control = Velocity Reduction / Distance Required
```

Elite players lose speed efficiently while maintaining balance.

```
   Elite:    ══════════════►▓▓│          ← sheds speed in a short distance
   Average:  ══════════════►▓▓▓▓▓▓▓│     ← needs more ground to stop
                            └─────┘
                       distance required
```

#### 4.3 Change-of-Direction Efficiency

Evaluates agility during shuttle and three-cone drills.

```
COD Efficiency = Heading Change / Time Lost
```

Higher scores indicate fluid directional transitions.

```
        Efficient cut                    Inefficient cut

   ──────────►╮                     ──────────►●  (stall)
              │  sharp heading                 ┊  rounded,
              │  change, little                ╰╮ time lost
              ▼  time lost                      ▼
```

#### 4.4 Movement Smoothness

Calculated by analysing acceleration variance throughout a drill.

Athletes with lower unnecessary movement variation may demonstrate better neuromuscular coordination.

```
 accel   Smooth (low variance)            Jerky (high variance)
   ▲                                        ▲
   │  ~~~~~~~~~~~~~~~~~~~~~                 │  /\  /\/\    /\  /\
   │                                        │ /  \/    \/\/  \/  \
   └───────────────────────► time           └───────────────────────► time
```

#### 4.5 Recovery Acceleration

Measures how quickly speed is regained following a change of direction.

Particularly important for:

- Pass rushers
- Receivers
- Defensive backs
- Offensive linemen

```
 speed
   ▲
   │ ────╮                ╭─────────
   │     ╲              ╱
   │      ╲           ╱   ← slope of re-acceleration
   │       ╲        ╱        = Recovery Acceleration
   │        ╰──●──╯
   └───────────┼────────────────────► time
          direction change
```

### Final MEI Score

```
MEI = 0.25 × Acceleration Efficiency
    + 0.20 × Deceleration Control
    + 0.25 × COD Efficiency
    + 0.15 × Movement Smoothness
    + 0.15 × Recovery Acceleration
```

```
 MEI component weights
 ───────────────────────────────────────────────────────────
 Acceleration Efficiency  │█████████████████████████ 25%
 COD Efficiency           │█████████████████████████ 25%
 Deceleration Control     │████████████████████      20%
 Movement Smoothness      │███████████████           15%
 Recovery Acceleration    │███████████████           15%
 ───────────────────────────────────────────────────────────
```

Scores are standardised by position group.

## 5. Position-Specific Analysis

The analysis covers the five position groups included in the Combine tracking data: wide receivers, tight ends, defensive backs, defensive linemen, and offensive linemen.

```
 Position          Combine signal (input)              NFL outcome (target)
 ─────────────────────────────────────────────────────────────────────────────
 Wide Receivers    route-transition mechanics   ───►   separation
 Tight Ends        burst, cuts & decel control  ───►   receiving value
 Defensive Backs   lateral agility              ───►   coverage effectiveness
 Defensive Linemen first-step burst             ───►   pass-rush success
 Offensive Linemen movement stability           ───►   pass-protection success
```

### 5.1 Wide Receivers

**Key Question:** Can Combine route-transition mechanics predict NFL separation?

| Combine Variables | NFL Outcomes |
|---|---|
| Deceleration rate | Average separation |
| Re-acceleration rate | EPA generated |
| Turning efficiency | Yards per route run |

**Expected finding:** Receivers with efficient direction changes demonstrate greater separation against NFL defenders.

### 5.2 Tight Ends

**Key Question:** Can Combine movement efficiency identify tight ends who win as receivers?

| Combine Variables | NFL Outcomes |
|---|---|
| Initial acceleration | Average separation |
| Change-of-direction efficiency | Yards per route run |
| Deceleration control | EPA generated |

**Expected finding:** Tight ends who combine high acceleration efficiency with strong deceleration control relative to other tight ends create more separation against linebackers and safeties.

### 5.3 Defensive Backs

**Key Question:** Can lateral agility predict coverage effectiveness?

| Combine Variables | NFL Outcomes |
|---|---|
| Backpedal efficiency | In-game break speed in man coverage |
| Hip turn speed | In-game closing speed in man coverage |
| Mirror movement score | Cushion |
| | Career defensive snaps |

**Expected finding:** Defensive backs demonstrating superior directional transition skills at the Combine break on the ball and close space faster in NFL man coverage.

### 5.4 Defensive Linemen

**Key Question:** Does first-step burst translate to pass-rush success?

| Combine Variables | NFL Outcomes |
|---|---|
| Initial acceleration | Pressure rate |
| Explosive force profile | Sack rate |
| Lateral engagement speed | In-game get-off |

**Expected finding:** Tracking-derived burst metrics outperform traditional 40-yard times.

### 5.5 Offensive Linemen

**Key Question:** Can movement stability predict pass protection success?

| Combine Variables | NFL Outcomes |
|---|---|
| Footwork consistency | Pressure allowed |
| Lateral movement efficiency | Sacks allowed |
| Recovery acceleration | Pass block efficiency |

**Expected finding:** Offensive linemen with consistent footwork and efficient lateral movement allow fewer pressures, while strong recovery acceleration helps them recover against counter moves from pass rushers.

## 6. Modelling Strategy

Three models are proposed.

```
 ┌───────────────────────┐  ┌───────────────────────┐  ┌───────────────────────┐
 │ MODEL 1: TRADITIONAL  │  │ MODEL 2: TRACKING     │  │ MODEL 3: HYBRID       │
 ├───────────────────────┤  ├───────────────────────┤  ├───────────────────────┤
 │ • 40-yard dash        │  │ • MEI                 │  │ • Traditional metrics │
 │ • Shuttle             │  │ • Acceleration profile│  │        +              │
 │ • Vertical            │  │ • Deceleration profile│  │ • Tracking metrics    │
 │ • Broad jump          │  │ • Angular velocity    │  │                       │
 ├───────────────────────┤  ├───────────────────────┤  ├───────────────────────┤
 │ Baseline benchmark    │  │ Tracking value alone  │  │ Combined power        │
 └───────────┬───────────┘  └───────────┬───────────┘  └───────────┬───────────┘
             └──────────────────────────┼──────────────────────────┘
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │ EVALUATION: R² · MAE · Cross-validation │
                    └─────────────────────────────────────────┘
```

### Model 1: Traditional Combine Metrics

- **Inputs:** 40-yard dash, Shuttle, Vertical, Broad jump
- **Purpose:** Baseline performance benchmark.

### Model 2: Tracking Metrics

- **Inputs:** MEI, Acceleration profile, Deceleration profile, Angular velocity
- **Purpose:** Determine tracking value independently.

### Model 3: Hybrid Model

- **Inputs:** Traditional metrics, Tracking metrics
- **Purpose:** Measure combined predictive power.

### Evaluation

**Metrics:**

- R²
- Mean Absolute Error
- Cross-validation

**Expected Outcome:** Hybrid models outperform traditional metrics alone.

## 7. Potential Findings

Several non-obvious insights may emerge.

**Finding 1: Top-end speed is less predictive than acceleration efficiency.**
Many NFL positions require short-area explosiveness rather than maximum velocity.

```
   Distance scale
   0 yd ├████████████████┤ 10 yd ············· 40 yd
         short-area burst   ← where acceleration matters most
```

**Finding 2: Deceleration is an underrated indicator of success.**
Elite route runners create separation because they stop faster than defenders.

```
   WR   ══════════►│◄═╗          WR stops sharply and breaks back
   DB   ═════════════════►│      DB overruns while decelerating
                   └──────┘
                  separation
```

**Finding 3: Movement symmetry predicts availability.**
Athletes exhibiting asymmetric movement patterns may be active for a smaller share of games.

```
   Left cut   ████████████████  100%
   Right cut  ███████████       70%   ← asymmetry flag
```

**Finding 4: Certain Combine drills contain hidden predictive value.**
Position-specific movement drills may be more informative than widely publicised measurements like the 40-yard dash.

## 8. Football Operations Impact

If validated, the proposed framework can assist NFL organisations in:

| Area | Application |
|---|---|
| **Draft Evaluation** | Identifying prospects who are more likely to succeed despite average traditional metrics. |
| **Player Development** | Designing position-specific training programs. |
| **Injury Prevention** | Detecting inefficient movement patterns. |
| **Contract Decisions** | Providing objective movement-based performance indicators. |

## 9. Conclusion

The NFL Big Data Bowl 2027 provides a unique opportunity to bridge pre-draft athletic evaluation and professional football performance by leveraging modern tracking technology. Rather than relying solely on traditional Combine results, this analysis introduces the Movement Efficiency Index (MEI), a tracking-based framework that captures acceleration, deceleration, direction changes, and movement quality.

The proposed approach aligns with the competition's goal of uncovering actionable, novel, and coach-friendly insights from Combine sensor data. If successful, the framework could help NFL teams identify hidden talent, improve player development, and make more informed draft decisions by focusing not only on how fast athletes move, but on **how efficiently they move**.
