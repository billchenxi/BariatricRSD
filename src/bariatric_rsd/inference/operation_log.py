"""
Surgical Operation Log Generator
=================================
Automatically generates structured intraoperative logs from BariatricRSD
model predictions. Runs in real-time alongside the model during surgery,
consuming phase/RSD/deviation outputs to produce timestamped clinical notes.

This is a clinical application layer on top of the multi-task model —
it does NOT require additional training. It converts the three prediction
streams into structured, human-readable surgical documentation.

Output format follows the Operative Report structure commonly used in
bariatric surgery documentation.

Usage:
    # Real-time (streaming inference)
    logger = OperationLogger(phase_names=["GPC", "GJA", "JJA"])
    for clip in video_stream:
        preds = model(clip, cluster_id)
        logger.update(timestamp, preds)
    report = logger.generate_report()

    # Post-hoc (from saved predictions)
    logger = OperationLogger.from_predictions(pred_file, phase_names)
    report = logger.generate_report()
"""

import json
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from pathlib import Path

import numpy as np


# ─── Data structures ───

@dataclass
class LogEvent:
    """A single timestamped event in the surgical operation log."""
    timestamp_sec: float
    event_type: str  # "phase_start", "phase_end", "deviation_start", "deviation_end", "rsd_milestone", "note"
    description: str
    phase: Optional[str] = None
    rsd_progress: Optional[float] = None
    deviation_score: Optional[float] = None
    confidence: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "time": self._format_time(self.timestamp_sec),
            "time_sec": round(self.timestamp_sec, 1),
            "type": self.event_type,
            "description": self.description,
            "phase": self.phase,
            "rsd_progress": round(self.rsd_progress, 3) if self.rsd_progress is not None else None,
            "deviation_score": round(self.deviation_score, 3) if self.deviation_score is not None else None,
            "confidence": round(self.confidence, 3) if self.confidence is not None else None,
        }

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Convert seconds to HH:MM:SS format."""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        return f"{h:02d}:{m:02d}:{s:02d}"


@dataclass
class PhaseSegment:
    """A continuous segment of a single surgical phase."""
    phase_name: str
    start_sec: float
    end_sec: float
    avg_rsd: float = 0.0
    max_deviation_score: float = 0.0
    num_deviations: int = 0

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec

    @property
    def duration_str(self) -> str:
        m = int(self.duration_sec // 60)
        s = int(self.duration_sec % 60)
        return f"{m}m {s}s"


@dataclass
class DeviationSegment:
    """A continuous segment where a deviation was detected."""
    start_sec: float
    end_sec: float
    phase: str
    peak_score: float
    avg_score: float
    description: str = ""

    @property
    def duration_sec(self) -> float:
        return self.end_sec - self.start_sec


# ─── Main Logger ───

class OperationLogger:
    """
    Real-time surgical operation logger.

    Consumes model predictions frame-by-frame and builds a structured
    timeline of surgical events including phase transitions, deviation
    alerts, and RSD milestones.
    """

    # RSD milestones to log (as fraction of total surgery)
    RSD_MILESTONES = [0.25, 0.50, 0.75, 0.90]

    # Deviation detection thresholds
    DEVIATION_THRESHOLD = 0.5
    DEVIATION_MIN_DURATION_SEC = 5.0  # minimum seconds to count as a real deviation

    # Phase smoothing: require N consecutive frames before logging a phase change
    PHASE_SMOOTHING_WINDOW = 5

    # Phase name aliases for readable reports
    PHASE_DISPLAY_NAMES = {
        "Gastric pouch creation": "Gastric Pouch Creation (GPC)",
        "Gastro-jejunal anastomosis": "Gastro-Jejunal Anastomosis (GJA)",
        "Jejuno-jejunal anastomosis": "Jejuno-Jejunal Anastomosis (JJA)",
        # Cholec80 phases
        "Preparation": "Preparation",
        "CalotTriangleDissection": "Calot Triangle Dissection",
        "ClippingCutting": "Clipping & Cutting",
        "GallbladderDissection": "Gallbladder Dissection",
        "GallbladderPackaging": "Gallbladder Packaging",
        "CleaningCoagulation": "Cleaning & Coagulation",
        "GallbladderRetraction": "Gallbladder Retraction",
    }

    def __init__(
        self,
        phase_names: List[str],
        procedure_type: str = "RYGB",
        surgeon_name: str = "",
        patient_id: str = "",
        deviation_threshold: float = 0.5,
        fps: float = 1.0,
    ):
        """
        Args:
            phase_names: List of surgical phase names.
            procedure_type: Type of surgical procedure.
            surgeon_name: Operating surgeon (for report header).
            patient_id: Patient identifier (for report header).
            deviation_threshold: Sigmoid probability threshold for deviation.
            fps: Effective frames per second of predictions.
        """
        self.phase_names = phase_names
        self.procedure_type = procedure_type
        self.surgeon_name = surgeon_name
        self.patient_id = patient_id
        self.deviation_threshold = deviation_threshold
        self.fps = fps

        # State tracking
        self.events: List[LogEvent] = []
        self.phase_segments: List[PhaseSegment] = []
        self.deviation_segments: List[DeviationSegment] = []

        # Running state
        self._current_phase: Optional[str] = None
        self._current_phase_start: float = 0.0
        self._phase_history: List[str] = []  # for smoothing
        self._in_deviation: bool = False
        self._deviation_start: float = 0.0
        self._deviation_scores: List[float] = []
        self._rsd_milestones_hit: set = set()
        self._last_timestamp: float = 0.0
        self._total_frames: int = 0
        self._finalized: bool = False

        # Accumulated predictions for summary stats
        self._all_rsd: List[Tuple[float, float]] = []  # (timestamp, rsd)
        self._all_deviations: List[Tuple[float, float]] = []  # (timestamp, score)
        self._all_phases: List[Tuple[float, str]] = []  # (timestamp, phase)

        # Log start
        self.start_time = datetime.datetime.now()
        self.events.append(LogEvent(
            timestamp_sec=0.0,
            event_type="note",
            description=f"Operation logging started — {procedure_type} procedure",
        ))

    def update(
        self,
        timestamp_sec: float,
        phase_pred: str,
        rsd_pred: float,
        deviation_score: float,
        phase_confidence: float = 1.0,
    ):
        """
        Process a single prediction frame and update the log.

        Args:
            timestamp_sec: Current timestamp in seconds.
            phase_pred: Predicted phase name.
            rsd_pred: Predicted RSD progress [0, 1].
            deviation_score: Deviation probability [0, 1].
            phase_confidence: Confidence of phase prediction.
        """
        if self._finalized:
            raise RuntimeError(
                "OperationLogger has already been finalized; create a new logger "
                "or avoid generating reports before streaming is complete."
            )

        self._last_timestamp = timestamp_sec
        self._total_frames += 1

        # Store raw predictions
        self._all_rsd.append((timestamp_sec, rsd_pred))
        self._all_deviations.append((timestamp_sec, deviation_score))
        self._all_phases.append((timestamp_sec, phase_pred))

        # Phase transition detection (with smoothing)
        self._update_phase(timestamp_sec, phase_pred, rsd_pred, phase_confidence)

        # Deviation detection
        self._update_deviation(timestamp_sec, deviation_score, phase_pred)

        # RSD milestones
        self._check_rsd_milestones(timestamp_sec, rsd_pred, phase_pred)

    def _update_phase(self, t: float, phase: str, rsd: float, conf: float):
        """Detect phase transitions with smoothing."""
        self._phase_history.append(phase)
        if len(self._phase_history) > self.PHASE_SMOOTHING_WINDOW:
            self._phase_history = self._phase_history[-self.PHASE_SMOOTHING_WINDOW:]

        # Check if majority of recent predictions agree on a new phase
        if len(self._phase_history) >= self.PHASE_SMOOTHING_WINDOW:
            majority_phase = max(set(self._phase_history), key=self._phase_history.count)
            majority_count = self._phase_history.count(majority_phase)

            if majority_count >= (self.PHASE_SMOOTHING_WINDOW * 0.6) and majority_phase != self._current_phase:
                # Phase transition detected
                if self._current_phase is not None:
                    # Close previous phase
                    self.events.append(LogEvent(
                        timestamp_sec=t,
                        event_type="phase_end",
                        description=f"Phase completed: {self._display_phase(self._current_phase)}",
                        phase=self._current_phase,
                        rsd_progress=rsd,
                    ))
                    self.phase_segments.append(PhaseSegment(
                        phase_name=self._current_phase,
                        start_sec=self._current_phase_start,
                        end_sec=t,
                    ))

                # Start new phase
                self._current_phase = majority_phase
                self._current_phase_start = t
                self.events.append(LogEvent(
                    timestamp_sec=t,
                    event_type="phase_start",
                    description=f"Phase started: {self._display_phase(majority_phase)}",
                    phase=majority_phase,
                    rsd_progress=rsd,
                    confidence=conf,
                ))

    def _update_deviation(self, t: float, score: float, phase: str):
        """Track deviation segments."""
        is_deviation = score >= self.deviation_threshold

        if is_deviation and not self._in_deviation:
            # Deviation started
            self._in_deviation = True
            self._deviation_start = t
            self._deviation_scores = [score]
        elif is_deviation and self._in_deviation:
            # Continuing deviation
            self._deviation_scores.append(score)
        elif not is_deviation and self._in_deviation:
            # Deviation ended — check if it was long enough
            duration = t - self._deviation_start
            if duration >= self.DEVIATION_MIN_DURATION_SEC:
                peak = max(self._deviation_scores)
                avg = sum(self._deviation_scores) / len(self._deviation_scores)

                seg = DeviationSegment(
                    start_sec=self._deviation_start,
                    end_sec=t,
                    phase=phase,
                    peak_score=peak,
                    avg_score=avg,
                    description=self._describe_deviation(phase, peak, duration),
                )
                self.deviation_segments.append(seg)

                self.events.append(LogEvent(
                    timestamp_sec=self._deviation_start,
                    event_type="deviation_start",
                    description=f"Deviation detected during {self._display_phase(phase)} (severity: {peak:.0%})",
                    phase=phase,
                    deviation_score=peak,
                ))
                self.events.append(LogEvent(
                    timestamp_sec=t,
                    event_type="deviation_end",
                    description=f"Deviation resolved — duration: {duration:.0f}s",
                    phase=phase,
                    deviation_score=avg,
                ))

            self._in_deviation = False
            self._deviation_scores = []

    def _check_rsd_milestones(self, t: float, rsd: float, phase: str):
        """Log when surgery passes key progress milestones."""
        for milestone in self.RSD_MILESTONES:
            if milestone not in self._rsd_milestones_hit and rsd >= milestone:
                self._rsd_milestones_hit.add(milestone)
                remaining_pct = (1.0 - rsd) * 100
                self.events.append(LogEvent(
                    timestamp_sec=t,
                    event_type="rsd_milestone",
                    description=f"Surgery {milestone:.0%} complete — estimated {remaining_pct:.0f}% remaining",
                    phase=phase,
                    rsd_progress=rsd,
                ))

    def _display_phase(self, phase: str) -> str:
        return self.PHASE_DISPLAY_NAMES.get(phase, phase)

    def _describe_deviation(self, phase: str, severity: float, duration: float) -> str:
        if severity > 0.8:
            level = "significant"
        elif severity > 0.6:
            level = "moderate"
        else:
            level = "minor"
        return f"{level.capitalize()} deviation during {self._display_phase(phase)} ({duration:.0f}s, peak severity {severity:.0%})"

    # ─── Finalize ───

    def finalize(self):
        """Call after the last frame to close any open segments."""
        if self._finalized:
            return

        t = self._last_timestamp

        # Close current phase
        if self._current_phase is not None:
            self.phase_segments.append(PhaseSegment(
                phase_name=self._current_phase,
                start_sec=self._current_phase_start,
                end_sec=t,
            ))

        # Close any open deviation
        if self._in_deviation and self._deviation_scores:
            duration = t - self._deviation_start
            if duration >= self.DEVIATION_MIN_DURATION_SEC:
                self.deviation_segments.append(DeviationSegment(
                    start_sec=self._deviation_start,
                    end_sec=t,
                    phase=self._current_phase or "Unknown",
                    peak_score=max(self._deviation_scores),
                    avg_score=sum(self._deviation_scores) / len(self._deviation_scores),
                ))

        self.events.append(LogEvent(
            timestamp_sec=t,
            event_type="note",
            description=f"Operation completed — total duration: {t / 60:.1f} minutes",
            rsd_progress=1.0,
        ))
        self._finalized = True

    # ─── Report Generation ───

    def generate_report(self) -> str:
        """
        Generate a structured operative report as plain text.

        Returns:
            Formatted surgical operation log string.
        """
        self.finalize()
        lines = []

        # Header
        lines.append("=" * 64)
        lines.append("  INTRAOPERATIVE OPERATION LOG")
        lines.append("  Automatically generated by BariatricRSD")
        lines.append("=" * 64)
        lines.append("")
        lines.append(f"  Procedure:    {self.procedure_type}")
        if self.surgeon_name:
            lines.append(f"  Surgeon:      {self.surgeon_name}")
        if self.patient_id:
            lines.append(f"  Patient ID:   {self.patient_id}")
        lines.append(f"  Date:         {self.start_time.strftime('%Y-%m-%d %H:%M')}")
        total_min = self._last_timestamp / 60
        lines.append(f"  Duration:     {total_min:.1f} minutes")
        lines.append(f"  Deviations:   {len(self.deviation_segments)} detected")
        lines.append("")

        # Phase summary
        lines.append("-" * 64)
        lines.append("  PHASE SUMMARY")
        lines.append("-" * 64)
        for seg in self.phase_segments:
            lines.append(
                f"  {LogEvent._format_time(seg.start_sec)} - "
                f"{LogEvent._format_time(seg.end_sec)}  "
                f"{self._display_phase(seg.phase_name):40s} "
                f"({seg.duration_str})"
            )
        lines.append("")

        # Deviation summary
        if self.deviation_segments:
            lines.append("-" * 64)
            lines.append("  DEVIATIONS DETECTED")
            lines.append("-" * 64)
            for i, dev in enumerate(self.deviation_segments, 1):
                lines.append(
                    f"  [{i}] {LogEvent._format_time(dev.start_sec)} - "
                    f"{LogEvent._format_time(dev.end_sec)}  "
                    f"Severity: {dev.peak_score:.0%}  "
                    f"Phase: {self._display_phase(dev.phase)}"
                )
                if dev.description:
                    lines.append(f"      {dev.description}")
            lines.append("")

        # Timeline
        lines.append("-" * 64)
        lines.append("  EVENT TIMELINE")
        lines.append("-" * 64)
        for event in sorted(self.events, key=lambda e: e.timestamp_sec):
            icon = {
                "phase_start": "[PHASE]",
                "phase_end": "[/PHASE]",
                "deviation_start": "[! DEV]",
                "deviation_end": "[DEV !]",
                "rsd_milestone": "[PROG]",
                "note": "[NOTE]",
            }.get(event.event_type, "[----]")
            lines.append(
                f"  {LogEvent._format_time(event.timestamp_sec)}  "
                f"{icon:10s} {event.description}"
            )
        lines.append("")
        lines.append("=" * 64)
        lines.append("  END OF OPERATION LOG")
        lines.append("=" * 64)

        return "\n".join(lines)

    def generate_json(self) -> dict:
        """Generate a structured JSON representation of the operation log."""
        self.finalize()
        return {
            "metadata": {
                "procedure": self.procedure_type,
                "surgeon": self.surgeon_name,
                "patient_id": self.patient_id,
                "date": self.start_time.isoformat(),
                "duration_sec": round(self._last_timestamp, 1),
                "total_frames": self._total_frames,
            },
            "phases": [
                {
                    "name": seg.phase_name,
                    "display_name": self._display_phase(seg.phase_name),
                    "start_sec": round(seg.start_sec, 1),
                    "end_sec": round(seg.end_sec, 1),
                    "duration_sec": round(seg.duration_sec, 1),
                }
                for seg in self.phase_segments
            ],
            "deviations": [
                {
                    "start_sec": round(dev.start_sec, 1),
                    "end_sec": round(dev.end_sec, 1),
                    "duration_sec": round(dev.duration_sec, 1),
                    "phase": dev.phase,
                    "peak_score": round(dev.peak_score, 3),
                    "avg_score": round(dev.avg_score, 3),
                    "description": dev.description,
                }
                for dev in self.deviation_segments
            ],
            "events": [e.to_dict() for e in sorted(self.events, key=lambda e: e.timestamp_sec)],
        }

    def save_report(self, output_dir: str, formats: List[str] = None):
        """
        Save the operation log in multiple formats.

        Args:
            output_dir: Directory to save files.
            formats: List of formats: "txt", "json". Default: both.
        """
        if formats is None:
            formats = ["txt", "json"]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        timestamp = self.start_time.strftime("%Y%m%d_%H%M")

        if "txt" in formats:
            txt_path = output_path / f"operation_log_{timestamp}.txt"
            txt_path.write_text(self.generate_report())
            print(f"Text report saved: {txt_path}")

        if "json" in formats:
            json_path = output_path / f"operation_log_{timestamp}.json"
            with open(json_path, "w") as f:
                json.dump(self.generate_json(), f, indent=2)
            print(f"JSON report saved: {json_path}")

    # ─── Factory ───

    @classmethod
    def from_predictions(
        cls,
        predictions_file: str,
        phase_names: List[str],
        procedure_type: str = "RYGB",
        fps: float = 1.0,
    ) -> "OperationLogger":
        """
        Create an OperationLogger from a saved predictions JSON file.

        Expected format:
            {"predictions": [{"timestamp": float, "phase": str, "rsd": float, "deviation": float}, ...]}
        """
        with open(predictions_file) as f:
            data = json.load(f)

        logger = cls(phase_names=phase_names, procedure_type=procedure_type, fps=fps)

        for pred in data["predictions"]:
            logger.update(
                timestamp_sec=pred["timestamp"],
                phase_pred=pred["phase"],
                rsd_pred=pred["rsd"],
                deviation_score=pred["deviation"],
                phase_confidence=pred.get("phase_confidence", 1.0),
            )

        return logger
