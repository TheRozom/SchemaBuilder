from functools import cached_property


class ServiceConfig:
    @cached_property
    def tree_builder(self):
        from src.bl.analyzer.trees import TreeBuilder

        return TreeBuilder()

    @cached_property
    def tree_comparator(self):
        from src.bl.analyzer.trees import TreeComparator

        return TreeComparator()

    @cached_property
    def ted_calculator(self):
        from src.bl.analyzer.trees import TedCalculator

        return TedCalculator()

    @cached_property
    def grouper(self):
        from src.bl.analyzer.groupers import Grouper

        return Grouper()

    @cached_property
    def similarity_calculator(self):
        from src.bl.analyzer.calculators import SimilarityCalculator

        return SimilarityCalculator()

    @cached_property
    def summary_generator(self):
        from src.bl.analyzer.generators import SummaryGenerator

        return SummaryGenerator()

    @cached_property
    def schema_merger(self):
        from src.bl.builder.mergers import SchemaMerger

        return SchemaMerger()

    @cached_property
    def bound_normalizer(self):
        from src.bl.builder.normalizers import BoundNormalizer

        return BoundNormalizer()

    @cached_property
    def error_formatter(self):
        from src.bl.validator.formatters import ErrorFormatter

        return ErrorFormatter()

    @cached_property
    def scoring_rule_registry(self):
        from src.bl.scoring.config import ScoringWeights
        from src.bl.scoring.registry import ScoringRuleRegistry
        from src.bl.scoring.rules.ambiguity import AmbiguityRule
        from src.bl.scoring.rules.completeness import CompletenessRule
        from src.bl.scoring.rules.security import SecurityRule
        from src.bl.scoring.rules.strictness import StrictnessRule

        weights = ScoringWeights()
        registry = ScoringRuleRegistry()

        security_rule = SecurityRule()

        registry.register("strictness", StrictnessRule(), weights.STRICTNESS)
        registry.register("completeness", CompletenessRule(), weights.COMPLETENESS)
        registry.register("ambiguity", AmbiguityRule(), weights.AMBIGUITY)
        registry.register("security", security_rule, weights.SECURITY)
        registry.register_security_rule(security_rule)

        return registry

    def reset(self):
        for attr in [
            "tree_builder",
            "tree_comparator",
            "ted_calculator",
            "grouper",
            "similarity_calculator",
            "summary_generator",
            "schema_merger",
            "bound_normalizer",
            "error_formatter",
            "scoring_rule_registry",
        ]:
            self.__dict__.pop(attr, None)


service_config = ServiceConfig()
