from src.core import load_yaml_config
from src.shared.models import AnalysisSummary, ConfidenceLevel, GroupData


class SummaryGenerator:
    def __init__(self) -> None:
        self.config = load_yaml_config("summary_thresholds.yaml")

    def generate(
        self, total: int, groups: list[GroupData], similarity: list[list[float]]
    ) -> AnalysisSummary:
        unique_count = len(groups)
        thresholds = self.config["summary_thresholds"]
        recommendations = self.config["recommendations"]

        if unique_count == 1:
            rec_config = recommendations["all_compatible"]
            recommendation = rec_config["message"].format(total=total)
            should_split = rec_config["should_split"]
            confidence = ConfidenceLevel[rec_config["confidence"]]

        elif unique_count == total:
            rec_config = recommendations["all_incompatible"]
            recommendation = rec_config["message"].format(total=total, unique_count=unique_count)
            should_split = rec_config["should_split"]
            confidence = ConfidenceLevel[rec_config["confidence"]]

        else:
            avg_similarity = (
                sum(sum(row) for row in similarity) / (total * total) if total > 0 else 0.0
            )

            if avg_similarity > thresholds["high_similarity"]["threshold"]:
                rec_config = recommendations["high_similarity"]
                recommendation = rec_config["message"].format(
                    unique_count=unique_count, avg_similarity=avg_similarity
                )
                should_split = rec_config["should_split"]
                confidence = ConfidenceLevel[rec_config["confidence"]]

            elif avg_similarity > thresholds["moderate_similarity"]["threshold"]:
                rec_config = recommendations["moderate_similarity"]
                recommendation = rec_config["message"].format(
                    unique_count=unique_count, avg_similarity=avg_similarity
                )
                should_split = rec_config["should_split"]
                confidence = ConfidenceLevel[rec_config["confidence"]]

            else:
                rec_config = recommendations["low_similarity"]
                recommendation = rec_config["message"].format(
                    unique_count=unique_count, avg_similarity=avg_similarity
                )
                should_split = rec_config["should_split"]
                confidence = ConfidenceLevel[rec_config["confidence"]]

        return AnalysisSummary(
            total_objects=total,
            unique_structures=unique_count,
            should_split_schemas=should_split,
            recommendation=recommendation,
            confidence=confidence,
        )
