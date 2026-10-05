"""
Metadata Filters Module

This module implements metadata filtering for retrieval.

Why we need metadata filtering:
- Restrict retrieval to specific document types
- Enable department-specific queries
- Support access control
- Improve retrieval precision

What it does:
- Creates filter objects from metadata dictionaries
- Applies filters during retrieval
- Supports exact match and other filter types
"""

from typing import Dict, Any, Optional, List
from llama_index.core.vector_stores import FilterCondition, MetadataFilters, MetadataFilter
from loguru import logger


class FilterManager:
    """
    Manager for creating and applying metadata filters.

    Why we need this class:
    - Centralize filter creation
    - Provide consistent filter interface
    - Support different filter types
    - Enable complex filter combinations

    What it does:
    - Creates filter objects from dictionaries
    - Supports exact match filters
    - Supports filter combinations (AND/OR)
    - Returns filter objects for retrievers
    """

    def create_filter(
        self,
        key: str,
        value: Any,
        operator: str = "==",
    ) -> MetadataFilter:
        """
        Create a single metadata filter.

        Why we need this method:
        - Create individual filters
        - Support different operators
        - Build complex filter combinations

        Args:
            key: Metadata field name
            value: Value to match
            operator: Comparison operator (==, !=, >, <, >=, <=, in, nin)

        Returns:
            MetadataFilter: Filter object

        What is MetadataFilter:
        - Represents a single filter condition
        - Specifies field, value, and operator
        - Used in MetadataFilters for combinations
        - Applied during retrieval to filter nodes

        Operators:
        - ==: Exact match
        - !=: Not equal
        - >, <, >=, <=: Numeric comparisons
        - in: Value in list
        - nin: Value not in list
        """

        logger.debug(f"Creating filter: {key} {operator} {value}")

        filter_obj = MetadataFilter(
            key=key,
            value=value,
            operator=operator,
        )

        return filter_obj

    def create_filters(
        self,
        filters_dict: Dict[str, Any],
        condition: str = "and",
    ) -> MetadataFilters:
        """
        Create metadata filters from a dictionary.

        Why we need this method:
        - Convert dict to filter objects
        - Support multiple filters
        - Combine with AND/OR logic

        Args:
            filters_dict: Dictionary of field=value pairs
            condition: How to combine filters ("and" or "or")

        Returns:
            MetadataFilters: Combined filter object

        What happens internally:
        1. Create individual filters for each key-value pair
        2. Combine them with specified condition
        3. Return MetadataFilters object

        Example:
        filters_dict = {"department": "HR", "document_category": "policy"}
        condition = "and"
        Result: Filter for HR AND policy documents
        """

        if not filters_dict:
            logger.debug("No filters provided")
            return None

        logger.info(f"Creating filters: {filters_dict} (condition={condition})")

        # Create individual filters
        filter_objects = []
        for key, value in filters_dict.items():
            filter_obj = self.create_filter(key, value)
            filter_objects.append(filter_obj)

        # Combine with condition
        filter_condition = (
            FilterCondition.AND if condition.lower() == "and" else FilterCondition.OR
        )

        metadata_filters = MetadataFilters(
            filters=filter_objects,
            condition=filter_condition,
        )

        logger.info(f"Created {len(filter_objects)} filters with {condition} condition")

        return metadata_filters

    def create_department_filter(
        self,
        department: str,
    ) -> MetadataFilters:
        """
        Create a filter for a specific department.

        Why we need this method:
        - Common use case: department-specific queries
        - Convenience method for department filtering
        - Example: "Show me HR leave policy"

        Args:
            department: Department name

        Returns:
            MetadataFilters: Filter for department
        """

        logger.info(f"Creating department filter: {department}")

        return self.create_filters({"department": department})

    def create_category_filter(
        self,
        category: str,
    ) -> MetadataFilters:
        """
        Create a filter for a specific document category.

        Why we need this method:
        - Common use case: category-specific queries
        - Convenience method for category filtering
        - Example: "Show me all policies"

        Args:
            category: Document category

        Returns:
            MetadataFilters: Filter for category
        """

        logger.info(f"Creating category filter: {category}")

        return self.create_filters({"document_category": category})


# Singleton instance
filter_manager = FilterManager()
