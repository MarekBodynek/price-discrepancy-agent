"""
Priority-based data merging.

Priority order (highest to lowest):
1. OCR (images)
2. Attachments (Excel, PDF text)
3. Email body
"""

from typing import Optional

from src.core.models import DataSource, ExtractedData


class PriorityMerger:
    """Merges extracted data according to source priority."""

    # Priority ranking (lower number = higher priority)
    SOURCE_PRIORITY = {
        DataSource.OCR: 1,
        DataSource.ATTACHMENT: 2,
        DataSource.BODY: 3,
    }

    def __init__(self):
        """Initialize merger."""
        pass

    def merge_field(
        self,
        extractions: list[ExtractedData],
        field_name: str,
        combine_lists: bool = False,
    ) -> tuple[Optional[any], list[str]]:
        """
        Merge a single field from multiple extractions using priority.

        Args:
            extractions: List of extracted data from different sources.
            field_name: Name of field to merge.
            combine_lists: If True, combine lists from all sources (for EANs).

        Returns:
            Tuple of (merged_value, conflicts) where conflicts lists alternative values.
        """
        if not extractions:
            return None, []

        # Sort by priority (OCR first)
        sorted_extractions = sorted(
            extractions,
            key=lambda e: self.SOURCE_PRIORITY.get(e.source, 999),
        )

        if combine_lists:
            # Combine all values from all sources (for EANs)
            all_values = []
            for ext in sorted_extractions:
                value = getattr(ext, field_name, None)
                if value and isinstance(value, list):
                    all_values.extend(value)

            # Remove duplicates while preserving order
            seen = set()
            unique_values = []
            for val in all_values:
                if val not in seen:
                    seen.add(val)
                    unique_values.append(val)

            return unique_values if unique_values else None, []

        # For single values, use highest priority
        primary_value = None
        primary_source = None
        conflicts = []

        for ext in sorted_extractions:
            value = getattr(ext, field_name, None)

            if value is not None:
                if primary_value is None:
                    # First non-null value (highest priority)
                    primary_value = value
                    primary_source = ext.source_details
                else:
                    # Conflict detected
                    if value != primary_value:
                        conflicts.append(
                            f"{ext.source_details}: {value} (overridden by {primary_source})"
                        )

        return primary_value, conflicts

    def merge_dict_field(
        self,
        extractions: list[ExtractedData],
        field_name: str,
    ) -> tuple[dict, list[str]]:
        """
        Merge dictionary field (e.g., EAN -> price mapping).

        Args:
            extractions: List of extracted data.
            field_name: Name of dict field.

        Returns:
            Tuple of (merged_dict, conflicts).
        """
        if not extractions:
            return {}, []

        # Sort by priority
        sorted_extractions = sorted(
            extractions,
            key=lambda e: self.SOURCE_PRIORITY.get(e.source, 999),
        )

        merged = {}
        conflicts = []

        # Iterate in reverse priority order, so highest priority overwrites
        for ext in reversed(sorted_extractions):
            dict_value = getattr(ext, field_name, None)

            if dict_value and isinstance(dict_value, dict):
                for key, value in dict_value.items():
                    if key in merged and merged[key] != value:
                        # Conflict
                        conflicts.append(
                            f"{field_name}[{key}]: {merged[key]} (from higher priority) "
                            f"vs {value} (from {ext.source_details})"
                        )
                    merged[key] = value

        return merged, conflicts

    def merge_all(
        self,
        extractions: list[ExtractedData],
    ) -> tuple[ExtractedData, list[str]]:
        """
        Merge all extractions into single ExtractedData.

        Args:
            extractions: List of extracted data from different sources.

        Returns:
            Tuple of (merged_data, all_conflicts).
        """
        if not extractions:
            # Return empty extraction
            return ExtractedData(
                source=DataSource.BODY,
                source_details="no data",
            ), []

        all_conflicts = []

        # Merge EANs (combine from all sources)
        eans, _ = self.merge_field(extractions, "eans", combine_lists=True)

        # Merge dates (priority-based)
        delivery_date, conf1 = self.merge_field(extractions, "delivery_date")
        all_conflicts.extend(conf1)

        order_creation_date, conf2 = self.merge_field(extractions, "order_creation_date")
        all_conflicts.extend(conf2)

        document_creation_date, conf3 = self.merge_field(extractions, "document_creation_date")
        all_conflicts.extend(conf3)

        # Merge supplier info (priority-based)
        supplier_name, conf4 = self.merge_field(extractions, "supplier_name")
        all_conflicts.extend(conf4)

        supplier_invoice_number, conf5 = self.merge_field(extractions, "supplier_invoice_number")
        all_conflicts.extend(conf5)

        # Merge price dicts (priority-based per EAN)
        supplier_prices, conf6 = self.merge_dict_field(extractions, "supplier_prices")
        all_conflicts.extend(conf6)

        internal_prices, conf7 = self.merge_dict_field(extractions, "internal_prices")
        all_conflicts.extend(conf7)

        stores, conf8 = self.merge_dict_field(extractions, "stores")
        all_conflicts.extend(conf8)

        # Determine primary source (highest priority with data)
        sorted_extractions = sorted(
            extractions,
            key=lambda e: self.SOURCE_PRIORITY.get(e.source, 999),
        )
        primary = sorted_extractions[0]

        merged = ExtractedData(
            source=primary.source,
            source_details=", ".join(e.source_details for e in sorted_extractions),
            eans=eans or [],
            delivery_date=delivery_date,
            order_creation_date=order_creation_date,
            document_creation_date=document_creation_date,
            supplier_name=supplier_name,
            supplier_invoice_number=supplier_invoice_number,
            supplier_prices=supplier_prices,
            internal_prices=internal_prices,
            stores=stores,
        )

        return merged, all_conflicts
