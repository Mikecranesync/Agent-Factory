#!/usr/bin/env python3
"""
TrendScoutAgent - Modern Visual Aesthetics & Trend Monitoring

Monitors viral industrial/manufacturing content to identify "oddly satisfying" patterns
and creates comprehensive style guide for channel consistency.

Responsibilities:
- Track viral industrial education content (YouTube, TikTok, Instagram)
- Identify "oddly satisfying" visual patterns (symmetry, precision, ASMR)
- Generate and maintain comprehensive CHANNEL_STYLE_GUIDE.md
- Monitor 2024-2025 trends (K-pop editing, mobile-first, minimalist)
- Balance consistency (80%) with creative variation (20%)
"""

import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class TrendScoutAgent:
    """
    Monitor trends and maintain channel visual aesthetic

    Creates comprehensive style guide with:
    - Color palettes
    - Typography rules
    - Motion design specs
    - Audio guidelines
    - Template systems
    """

    def __init__(self, project_root: Path = None):
        """Initialize agent"""
        self.agent_name = "trend_scout_agent"
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.style_guide_path = self.project_root / "docs" / "CHANNEL_STYLE_GUIDE.md"

        # 2024-2025 Viral Pattern Database (from research)
        self.viral_patterns = {
            "oddly_satisfying": [
                "Symmetry reveals (bilateral, radial, rotational)",
                "Precision manufacturing shots (tight tolerances, perfect fits)",
                "Slow-motion mechanics (gears meshing, fluid motion)",
                "ASMR elements (subtle machinery sounds, texture focus)",
                "Grid overlays and measurement callouts",
                "Repetitive motions (hypnotic loops, synchronized actions)",
                "Before/after transformations",
                "Satisfying endings (perfect alignment, clean completion)"
            ],
            "2025_editing_trends": [
                "K-pop-inspired: Synchronized cuts to audio beats",
                "K-pop-inspired: Rhythmic repetitions for emphasis",
                "K-pop-inspired: Vibrant color grading shifts",
                "Mobile-first: 9:16 vertical framing",
                "Mobile-first: Text at top/bottom (thumb zones)",
                "Minimalist: Clean, high-contrast visuals",
                "Minimalist: White space for focus",
                "ASMR-tinged: Whispering narrations over visuals"
            ],
            "psychological_hooks": [
                "Dopamine triggers: Perfect timing, satisfying loops",
                "Serotonin release: Positive completion moments",
                "Curiosity gaps: Show problem, delay solution 3-5s",
                "Pattern recognition: Symmetry activates visual cortex",
                "Tactile simulation: Texture close-ups trigger mirror neurons"
            ]
        }

    def generate_style_guide(self) -> str:
        """
        Generate comprehensive 30-page style guide.

        Returns:
            Path to generated style guide
        """
        logger.info("Generating comprehensive style guide...")

        style_guide_content = self._build_style_guide_content()

        # Ensure docs directory exists
        self.style_guide_path.parent.mkdir(parents=True, exist_ok=True)

        # Write style guide
        with open(self.style_guide_path, 'w', encoding='utf-8') as f:
            f.write(style_guide_content)

        logger.info(f"Style guide generated: {self.style_guide_path}")
        return str(self.style_guide_path)

    def _build_style_guide_content(self) -> str:
        """Build complete style guide markdown content"""

        return f"""# CHANNEL STYLE GUIDE
## Industrial Education Content - Modern Aesthetic Standards

**Generated:** {datetime.now().strftime("%Y-%m-%d")}
**Version:** 1.0
**Agent:** TrendScoutAgent

---

## Table of Contents

1. [Overview & Philosophy](#overview)
2. [Color System](#colors)
3. [Typography](#typography)
4. [Motion Design](#motion)
5. [Audio Design](#audio)
6. [Visual Templates](#templates)
7. ["Oddly Satisfying" Patterns](#satisfying)
8. [Content Formatting](#formatting)
9. [Variation Guidelines](#variation)
10. [2025 Trend Integration](#trends)

---

## 1. Overview & Philosophy {{#overview}}

### Core Principles
1. **Precision & Clarity** - Industrial content demands accuracy
2. **Satisfying Aesthetics** - Leverage psychological triggers (symmetry, completion)
3. **Modern Minimalism** - Clean, high-contrast, uncluttered
4. **Mobile-First** - 70%+ views on phones, optimize for 9:16
5. **Template Consistency** - 80% adherence, 20% creative variation

### Target Audience Psychology
- **Technicians:** Want accurate, no-BS info
- **Apprentices:** Need clear, step-by-step visuals
- **Hobbyists:** Inspired by "cool factor" and satisfying visuals
- **Students:** Engage with modern editing, fast pacing

---

## 2. Color System {{#colors}}

### Primary Palette
- **Industrial Blue:** `#1E3A8A` (Deep blue, trustworthy, technical)
- **Safety Orange:** `#F97316` (Accent, warnings, emphasis)

### Secondary Palette
- **Neutral Dark:** `#1F2937` (Backgrounds, text blocks)
- **Neutral Light:** `#F3F4F6` (Light backgrounds, contrast)
- **Success Green:** `#10B981` (Correct answers, completions)
- **Warning Yellow:** `#F59E0B` (Caution, important notes)
- **Error Red:** `#EF4444` (Errors, dangers, stop actions)

### Usage Rules
- **Backgrounds:** 90% neutral (dark for videos, light for diagrams)
- **Text:** High contrast only (white on dark, dark on light)
- **Accents:** Safety Orange for CTAs, callouts, emphasis (max 10% of frame)
- **Color Grading:** Slight desaturation for realism, vibrant accents for emphasis

### Color Psychology
- Blue = Reliability, technical expertise
- Orange = Energy, attention, action
- Green = Success, go ahead, correct
- Red = Stop, danger, error

---

## 3. Typography {{#typography}}

### Font Stack
**Primary (Headings, Titles):**
- Font: **Roboto Condensed Bold**
- Sizes: 72pt (title cards), 48pt (section headers), 36pt (subheads)
- Weight: 700 (Bold)
- Tracking: -2% (tight, industrial feel)

**Secondary (Body, Captions):**
- Font: **Inter Regular**
- Sizes: 28pt (main text), 20pt (captions), 16pt (annotations)
- Weight: 400 (Regular), 600 (Semi-bold for emphasis)
- Line Spacing: 1.4x (readable on mobile)

### Typography Rules
- **Max 3 lines per text card** (mobile readability)
- **All caps for titles** (TITLE LIKE THIS)
- **Sentence case for body** (Body text like this)
- **No center-align for paragraphs** (left-align body text)
- **Drop shadow for text over video** (2px black shadow, 80% opacity)

### Text Animation Timing
- Fade in: 0.2s
- Hold: Minimum 3s (reading time: 3s per line)
- Fade out: 0.2s
- Slide in from left: 0.3s with ease-out

---

## 4. Motion Design {{#motion}}

### Transition Timing
- **Fade:** 0.3s (standard transition)
- **Cross-dissolve:** 0.5s (between major sections)
- **Hard cut:** 0s (on beat, for energy)
- **Zoom in:** 0.4s (focus on detail)
- **Slide wipe:** 0.3s (horizontal, left to right)

### Animation Principles
- **Ease curves:** Always use ease-in-out (no linear)
- **Anticipation:** 0.1s pause before major transitions
- **Follow-through:** 0.1s overshoot on zoom/slide, then settle
- **Slow-motion:** 50% speed for satisfying moments (gears meshing, perfect fits)

### Camera Movements
- **Push in:** Slow zoom (3s duration) to focus on detail
- **Pull out:** Reveal context after detail shot
- **Pan:** Smooth, 2-3s duration, follow action
- **Static:** Hold on satisfying visuals for 3-5s (let viewer absorb)

### Visual Effects
- **Grid overlay:** Subtle 10x10 grid, 20% opacity, for precision shots
- **Measurement callouts:** Animated lines with dimensions (0.3s draw)
- **Highlight glow:** 5px orange glow around important elements
- **Motion blur:** 2-frame blur on fast movements (more cinematic)

---

## 5. Audio Design {{#audio}}

### Music Guidelines
- **Genre:** Electronic minimal, lo-fi beats, ambient industrial
- **BPM Range:** 100-120 (energetic but not frantic)
- **Volume:** -18dB (background, never overpowers narration)
- **Cuts:** Always on beat (align transitions to music)

### Narration Style
- **Voice:** Calm, authoritative, friendly (Edge-TTS: Guy)
- **Pace:** 140-150 WPM (words per minute)
- **Pauses:** 0.5s between sentences, 1s between sections
- **Emphasis:** Slight volume increase (+2dB) on key terms

### Sound Effects
- **Transition whoosh:** Subtle, -12dB
- **Reveal sound:** Satisfying "pop" or "click", -10dB
- **Error beep:** Clear, attention-grabbing, -8dB
- **Success chime:** Positive, brief, -10dB

### ASMR Integration
- **Machinery sounds:** Authentic, captured at source, -15dB
- **Texture focus:** Amplify subtle sounds (screws tightening, switches clicking)
- **Foley:** Add satisfying sounds to silent moments

---

## 6. Visual Templates {{#templates}}

### Template 1: Title Card
```
[Black background]
[Title text: Roboto Condensed Bold, 72pt, white]
[Subtitle: Inter Regular, 28pt, gray-400]
[Duration: 3s]
```

### Template 2: Step Card
```
[Dark blue background #1E3A8A]
[Step number: Circle, orange, top-left]
[Step title: Roboto 48pt, white]
[Step description: Inter 28pt, 3 lines max, gray-200]
[Visual: 60% of frame, right side]
[Duration: 5-7s]
```

### Template 3: Callout Card
```
[Semi-transparent overlay on video]
[Highlight box: Orange border, 4px]
[Callout text: Inter Semi-bold, 32pt]
[Arrow pointing to relevant area]
[Duration: 4s]
```

### Template 4: Before/After Comparison
```
[Split screen: 50/50 vertical divide]
[Left: "BEFORE" label, red]
[Right: "AFTER" label, green]
[Synchronized playback]
[Duration: 6-8s]
```

### Template 5: Outro CTA
```
[Dark background]
[CTA text: "Want more? Subscribe!" - Roboto 48pt]
[Subscribe button graphic]
[Next video preview: 30% of frame, bottom-right]
[Duration: 5s]
```

---

## 7. "Oddly Satisfying" Patterns {{#satisfying}}

### Symmetry Reveals
- **Bilateral:** Perfect mirror images (motor assemblies, control panels)
- **Radial:** Circular patterns (gears, rotors, bearings)
- **Rotational:** 360-degree spins showing perfect balance

**Implementation:**
- Start asymmetric, reveal symmetry over 2-3s
- Slow-motion (50% speed) during reveal
- Grid overlay to emphasize precision

### Precision Moments
- **Perfect Fits:** Close-ups of components sliding into place (0.001" tolerance)
- **Alignment:** Showing perfect parallel lines, right angles, concentricity
- **Tight Tolerances:** Machined surfaces, smooth finishes, mirror polish

**Implementation:**
- Zoom in 200% on moment of perfection
- Hold for 2-3s (let satisfaction sink in)
- Subtle "click" sound effect

### Repetitive Hypnotic Loops
- **Synchronized Machines:** Multiple units operating in unison
- **Rhythmic Motions:** Conveyor belts, pistons, rotating assemblies
- **Perfect Timing:** Actions synced to music beat

**Implementation:**
- Loop 3-5 times before moving on
- Match loop timing to music BPM
- Slight speed ramp (98% → 100% → 98%) for organic feel

### Satisfying Endings
- **Clean Completion:** Part fully assembled, circuit fully tested
- **Before/After:** Dirty → Clean, Broken → Fixed, Chaos → Order
- **Final Click:** Latch closing, button pressing, switch flipping

**Implementation:**
- Always end tutorials with satisfying completion shot
- Hold on final state for 3s
- Success chime sound effect

---

## 8. Content Formatting {{#formatting}}

### Shorts (<60s)
- **Structure:** Hook (0-3s) → Concept (4-40s) → Payoff (41-60s)
- **Hook examples:**
  - "This mistake costs $10K..."
  - "You've been doing this wrong..."
  - Immediate visual grab (explosion, failure, precision shot)
- **Pacing:** Fast cuts (3-5s per shot), energetic music
- **Payoff:** Satisfying conclusion, clear answer, visual wow

### Tutorials (5-10 min)
- **Structure:** Intro (0-30s) → Steps (1-2 min each) → Recap (last 30s)
- **Intro:** Problem statement + what you'll learn
- **Steps:** Title card → demonstration → key points overlay
- **Recap:** Summarize 3-5 main points, CTA

### Series (3-5 episodes)
- **Episode Structure:** Recap previous (15s) → New concept → Cliff hanger/teaser for next
- **Progression:** Simple → Complex (each episode builds on previous)
- **Callbacks:** Reference previous episodes visually (show earlier clips)

---

## 9. Variation Guidelines {{#variation}}

### 80% Template Adherence
- Always use approved color palette
- Always follow typography rules
- Always hit minimum duration requirements

### 20% Creative Variation
**Allowed Variations:**
- **Transition style:** Mix fades, wipes, cuts (but keep timing)
- **Camera angles:** Different perspectives on same subject
- **Music tempo:** Vary BPM ±10 for mood
- **Visual metaphors:** Creative analogies for concepts
- **Seasonal themes:** Holiday colors (10% accent only)

**Forbidden Variations:**
- Don't change color palette hex codes
- Don't use off-brand fonts
- Don't break accessibility rules (contrast, readability)
- Don't violate pacing rules (text hold times)

---

## 10. 2025 Trend Integration {{#trends}}

### K-Pop Editing Style
- **Synchronized Cuts:** Align every cut to music beat (use BPM calculator)
- **Rhythmic Repetitions:** Show same action 3x with slight variations
- **Vibrant Shifts:** Quick color grade changes (warm → cool → neutral)

**When to use:** High-energy shorts, satisfying compilations

### Mobile-First Framing
- **9:16 Vertical:** Default aspect ratio for shorts
- **Thumb Zones:** CTA buttons at bottom 1/3 of screen
- **Text Placement:** Top 1/3 or bottom 1/3 (avoid center)

**When to use:** All shorts, mobile-targeted content

### Minimalist Aesthetics
- **White Space:** 30-40% of frame is empty (focus viewer attention)
- **Single Focus:** One element per frame (don't clutter)
- **High Contrast:** Pure black/white for impact

**When to use:** Concept explanations, diagrams, technical breakdowns

### ASMR-Tinged Narration
- **Whisper Mode:** Soft narration over machinery sounds
- **Pause for Ambient:** Let machine sounds play solo for 2-3s
- **Layered Audio:** Narration + subtle machine + minimal music

**When to use:** Detailed procedures, relaxing/satisfying content

---

## Compliance Checklist

Before publishing ANY video, verify:

- [ ] Colors from approved palette only
- [ ] Typography follows size/weight rules
- [ ] Transitions within timing ranges (0.2-0.5s)
- [ ] Text readable for minimum duration (3s per line)
- [ ] Audio mixed properly (narration > SFX > music)
- [ ] At least one "oddly satisfying" moment
- [ ] Mobile-first framing considered
- [ ] 80% template adherence maintained
- [ ] Accessible (captions, high contrast, clear audio)
- [ ] Brand safe (no controversial imagery/sound)

---

## Update Schedule

- **Monthly:** TrendScoutAgent reviews viral content, proposes updates
- **Quarterly:** Design Committee votes on major aesthetic shifts
- **Yearly:** Full style guide overhaul based on platform changes

**Last Updated:** {datetime.now().strftime("%Y-%m-%d")}
**Next Review:** {datetime.now().strftime("%Y-%m-15")}

---

*This style guide is maintained by TrendScoutAgent and approved by Design Committee.*
*For questions or proposed changes, consult committee voting system.*
"""

    def analyze_viral_patterns(self, sample_urls: List[str] = None) -> Dict[str, Any]:
        """
        Analyze viral industrial content for patterns.

        Args:
            sample_urls: URLs to analyze (optional)

        Returns:
            Analysis report with identified patterns
        """
        # For MVP, return pre-researched patterns
        # In production, this would scrape and analyze actual videos

        report = {
            "analysis_date": datetime.now().isoformat(),
            "viral_patterns_identified": self.viral_patterns,
            "trend_summary": {
                "top_pattern": "Symmetry reveals with slow-motion",
                "rising_trend": "K-pop-inspired rhythmic editing",
                "declining_trend": "Long intro sequences (viewers skip)",
                "recommendation": "Focus on immediate hooks (<3s) and satisfying visual loops"
            },
            "sample_channels_analyzed": [
                "Practical Engineering (clarity + production quality)",
                "How It's Made (satisfying manufacturing shots)",
                "ElectroBOOM (engaging personality + technical depth)",
                "Technology Connections (detailed explanations + visuals)",
                "Smarter Every Day (slow-motion + curiosity-driven)"
            ]
        }

        return report

    def get_style_compliance_score(self, video_analysis: Dict) -> float:
        """
        Score a video's compliance with style guide (0-10 scale).

        Args:
            video_analysis: Dict with video characteristics

        Returns:
            Compliance score (0-10)
        """
        # Placeholder for future implementation
        # Would analyze actual video file for color palette, typography, timing, etc.
        return 8.5


if __name__ == "__main__":
    # Demo: Generate style guide
    agent = TrendScoutAgent()

    print("=" * 70)
    print("TREND SCOUT AGENT - STYLE GUIDE GENERATION")
    print("=" * 70)

    # Generate comprehensive style guide
    style_guide_path = agent.generate_style_guide()
    print(f"\n[OK] Style guide generated: {style_guide_path}")

    # Analyze viral patterns
    patterns = agent.analyze_viral_patterns()
    print(f"\n[OK] Viral patterns analyzed")
    print(f"  Top pattern: {patterns['trend_summary']['top_pattern']}")
    print(f"  Rising trend: {patterns['trend_summary']['rising_trend']}")
    print(f"  Recommendation: {patterns['trend_summary']['recommendation']}")

    print("\n" + "=" * 70)
    print("Style guide ready for Design Committee review!")
    print("=" * 70)
