# Feature 1: Multi-Character Composition with Adaptive Phrase Boost — Final Plan

## Core Conclusion

After analyzing successful IBus engines (libpinyin, chewing), general knowledge from training data, and segmentation reliability challenges, the optimal approach combines proven language model techniques with intelligent fallback mechanisms to handle the inherent uncertainty in stroke segmentation.

## Key Insights

### From IBus Engine Comparisons
- **libpinyin/libzhuyin/chewing** prove that n-gram language models significantly improve input accuracy
- **Fundamental similarity**: All successful engines use context to boost likely sequences
- **Critical adaptation**: We apply this principle to stroke space (strokes → segments → recognition → combination → language model filtering) rather than phonetic space
- **Key takeaway**: The language model approach is sound; our challenge is implementing it reliably in the stroke domain

### From Training Data Knowledge
- **Beam search** is standard practice in recognition systems for managing combinatorial complexity
- **Log-linear combination** of observation and language model scores is well-established
- **Segmentation reliability** is consistently identified as the weakest link in stroke-based systems
- **Fallback mechanisms** are essential for robustness in real-world usage

### From Practical Implementation Concerns
- **Runtime dependencies** complicate deployment and licensing
- **Performance targets** (<100ms candidate generation) critical for user experience
- **Build-time extraction** avoids runtime dependency/licensing issues

## Recommended Approach: Adaptive C1+ with Confidence-Based Fallback

### Phase 1: Segmentation Confidence Assessment

Before committing to complex processing, evaluate segmentation reliability:

```
confidence_score = f(
    stroke_density_consistency,
    gap_uniformity_measure,
    stroke_timing_patterns,
    y_overlap_analysis
)
```

- **High confidence** (score ≥ 0.7): Proceed to C1+ processing
- **Low confidence** (score < 0.7): Fallback to single-character mode (V1 behavior)

This directly addresses the segmentation reliability weakness identified in all comparisons.

### Phase 2: Adaptive Processing

#### A. High Confidence Path: C1+ with Beam Search & Phrase Boost

1. **Spatial Segmentation**: Detect character clusters using X-gaps with adaptive thresholds
2. **Recognition per Segment**: For each cluster, run Zinnia recognition retrieving top-L candidates
3. **Beam Search with Phrase Boost**:

```
beam = [("", 0.0)]
for segment i from 1 to k:
    new_beam = []
    for prefix, prefix_score in beam:
        for (char, z_score) in segment_i_candidates:
            new_prefix = prefix + char
            zinnia_component = log(z_score)
            phrase_component = PHRASE_BOOST_WEIGHT * log(phrase_freq.get(new_prefix, 1.0))
            length_penalty = LENGTH_PENALTY_WEIGHT * len(new_prefix)
            total_score = prefix_score + zinnia_component + phrase_component - length_penalty
            new_beam.append((new_prefix, total_score))
    beam = sorted(new_beam, key=lambda x: x[1], reverse=True)[:BEAM_WIDTH]
```

4. **Candidate Presentation**: Show top-N full phrases (e.g., "我们是", "我爱你")

#### B. Low Confidence Path: Fallback to V1 Behavior

- Process entire stroke sequence as single unit
- Standard Zinnia recognition → immediate commit on candidate selection
- Identical to current V1 behavior

### Phase 3: Data Utilization

- **Source**: Extract 2- and 3-character frequencies from libpinyin's `model20.text.tar.gz`
- **Process** (build-time extraction):
  1. Download `model20.text.tar.gz` from SourceForge
  2. Parse `.table` files (format: `<text>\t<pinyin>\t<frequency>`)
  3. Filter for entries where 1 ≤ text length ≤ 3
  4. Convert to log-frequency scores
  5. Save as JSON: `{"的地": 5.45, "一心": 5.87, "我们是": 5.22, ...}`
- **Usage**: `phrase_freq.get(phrase, 0.0)` returns 0.0 for unseen phrases (no boost)
- **Size Control**: Limit to top 75k phrases (~1.2MB JSON)

### Phase 4: UI Adaptations

- **Dynamic Candidate Display**: Show mixed 1-4 character phrases in high confidence mode
- **Text Handling**: Left-aligned text, automatic elision for overly long phrases
- **Confidence Feedback**: Subtle background hue shift (greenish for high confidence, neutral for low)

### Phase 5: User Control

- Settings toggle to enable/disable phrase boost
- Adjustable confidence threshold
- Opt-in session logging for future improvement
- Intuitive backspace behavior per mode

## Success Criteria

### Phase 1: Core Functionality
- [ ] High confidence path correctly processes reliable segmentations
- [ ] Common phrases ("我爱你", "我们是") receive appropriate boost
- [ ] Beam search completes within <80ms on target hardware
- [ ] Falls back to low confidence path when segmentation uncertain
- [ ] Low confidence path functions identically to V1

### Phase 2: Quality & Performance
- [ ] Phrase boosting improves accuracy for common multi-character inputs
- [ ] No significant memory increase (<2.5MB additional)
- [ ] UI remains responsive during computation (<16ms frame time)

### Phase 3: Regression Prevention
- [ ] Single-character input works identically to V1 when boost disabled
- [ ] All existing features (ESC pause/resume, delete, trackpad, window positioning) unchanged
- [ ] No crashes in edge cases (empty strokes, single rapid tap, etc.)

### Phase 4: UX Validation
- [ ] Target audience testing shows reduced strokes per character for multi-character input
- [ ] Users feel the system "anticipates" common phrases naturally
- [ ] Power users can disable boost for V1-like behavior
- [ ] New users find multi-character flow intuitive

## Best Elements from All Comparisons

| Source | Element Incorporated | Application |
|--------|---------------------|-------------|
| IBus Engines | Language model effectiveness | Adapted to stroke space with confidence gating |
| Training Data | Beam search + log-linear combination | Standard techniques with domain-appropriate parameters |
| Segmentation Analysis | Fallback for unreliability | Confidence-based adaptive processing (core innovation) |
| Practical Concerns | Build-time data extraction | No runtime dependencies, preserves data quality |
| UI/UX Studies | Graceful degradation | Advanced when beneficial, simple fallback when not |

## Implementation Philosophy

This plan creates an **intelligent adaptive system** that:
1. **Attempts advanced processing** only when likely to succeed
2. **Gracefully degrades** to proven reliable methods when uncertain
3. **Puts user in control** through adjustable settings
4. **Learns from usage** through opt-in session logging
5. **Respects practical constraints** through build-time extraction and performance budgets
