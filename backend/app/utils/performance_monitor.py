"""
Performance monitoring utilities for tracking resume processing times
"""
import time
from typing import Dict
from collections import defaultdict

class PerformanceMonitor:
    """Track processing times for each stage"""
    
    _timings: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    @classmethod
    def start_stage(cls, resume_id: str, stage: str):
        """Start timing a stage"""
        if resume_id not in cls._timings:
            cls._timings[resume_id] = {}
        cls._timings[resume_id][f"{stage}_start"] = time.time()
    
    @classmethod
    def end_stage(cls, resume_id: str, stage: str):
        """End timing a stage and calculate duration"""
        if resume_id in cls._timings:
            start_key = f"{stage}_start"
            if start_key in cls._timings[resume_id]:
                start_time = cls._timings[resume_id][start_key]
                duration = time.time() - start_time
                cls._timings[resume_id][stage] = duration
                print(f"[TIMING] {resume_id} - {stage}: {duration:.2f}s")
                return duration
        return 0
    
    @classmethod
    def get_summary(cls, resume_id: str) -> Dict[str, float]:
        """Get timing summary for a resume"""
        if resume_id in cls._timings:
            return {k: v for k, v in cls._timings[resume_id].items() if not k.endswith('_start')}
        return {}
    
    @classmethod
    def print_summary(cls, resume_id: str):
        """Print timing summary"""
        summary = cls.get_summary(resume_id)
        if summary:
            total = sum(summary.values())
            print(f"\n[TIMING SUMMARY] {resume_id}")
            print(f"Total time: {total:.2f}s")
            for stage, duration in sorted(summary.items(), key=lambda x: x[1], reverse=True):
                percentage = (duration / total * 100) if total > 0 else 0
                print(f"  {stage}: {duration:.2f}s ({percentage:.1f}%)")
            print()
    
    @classmethod
    def clear(cls, resume_id: str):
        """Clear timings for a resume"""
        if resume_id in cls._timings:
            del cls._timings[resume_id]
