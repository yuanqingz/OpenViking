# Copyright (c) 2026 Beijing Volcano Engine Technology Co., Ltd.
# SPDX-License-Identifier: AGPL-3.0
"""Dependency-light schema builder for OpenViking context collections."""

from typing import Any, Dict, Optional


def build_context_collection_schema(
    name: str, vector_dim: int, description: Optional[str] = None
) -> Dict[str, Any]:
    """Return the canonical schema for an OpenViking context collection."""

    fields = [
        {"FieldName": "id", "FieldType": "string", "IsPrimaryKey": True},
        {"FieldName": "uri", "FieldType": "path"},
        {"FieldName": "type", "FieldType": "string"},
        {"FieldName": "context_type", "FieldType": "string"},
        {"FieldName": "vector", "FieldType": "vector", "Dim": vector_dim},
        {"FieldName": "sparse_vector", "FieldType": "sparse_vector"},
        {"FieldName": "created_at", "FieldType": "date_time"},
        {"FieldName": "updated_at", "FieldType": "date_time"},
        {"FieldName": "active_count", "FieldType": "int64"},
        {"FieldName": "level", "FieldType": "int64"},
        {"FieldName": "name", "FieldType": "string"},
        {"FieldName": "description", "FieldType": "string"},
        {"FieldName": "tags", "FieldType": "string"},
        {"FieldName": "search_tags", "FieldType": "list<string>"},
        {"FieldName": "abstract", "FieldType": "string"},
        {"FieldName": "content", "FieldType": "text"},
        {"FieldName": "account_id", "FieldType": "string"},
        {"FieldName": "owner_user_id", "FieldType": "string"},
    ]
    scalar_index = [
        "uri",
        "type",
        "context_type",
        "created_at",
        "updated_at",
        "active_count",
        "level",
        "name",
        "tags",
        "search_tags",
        "account_id",
        "owner_user_id",
    ]
    return {
        "CollectionName": name,
        "Description": description or "Unified context collection",
        "Fields": fields,
        "ScalarIndex": scalar_index,
        "FullText": [
            {
                "Field": "content",
                "Analyzer": {"Tokenizer": "standard", "StopWordsFilters": ["symbol"]},
            },
        ],
    }
