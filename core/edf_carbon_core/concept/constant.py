"""Carbon Constant"""

from dataclasses import dataclass, field

from edf_fusion.concept import Constant as FusionConstant
from edf_fusion.helper.logging import get_logger

from .category import TASK_CATEGORY, Category
from .search_pattern import SearchPattern

_LOGGER = get_logger('core.concept.constant', root='carbon')


@dataclass(kw_only=True)
class Constant(FusionConstant):
    """Carbon Constant"""

    categories: dict[str, Category] = field(default_factory=dict)
    search_patterns: list[SearchPattern] = field(default_factory=list)

    @classmethod
    def from_dict(cls, dct):
        constant = super().from_dict(dct)
        for category in dct.get('categories', []):
            category = Category.from_dict(category)
            if category.name in constant.categories:
                _LOGGER.warning("duplicate category: %s", category.name)
                continue
            constant.categories[category.name] = category
        # ensure TASK category exists
        if TASK_CATEGORY.name not in constant.categories:
            constant.categories[TASK_CATEGORY.name] = TASK_CATEGORY
        constant.search_patterns = [
            SearchPattern.from_dict(item)
            for item in dct.get('search_patterns', [])
        ]
        return constant

    def to_dict(self):
        dct = super().to_dict()
        dct.update(
            {
                'categories': [
                    category.to_dict() for category in self.categories.values()
                ],
                'search_patterns': [
                    search_pattern.to_dict()
                    for search_pattern in self.search_patterns
                ],
            }
        )
        return dct
