"""Compare schema 兼容性测试"""
from app.schemas.compare import CreateTaskRequest


def test_create_task_request_supports_batch_only_incremental_config():
    payload = {
        "source_id": "src-1",
        "target_id": "tgt-1",
        "table_selection": {"mode": "mapping", "tables": []},
        "options": {
            "mode": "incremental",
            "incremental_config": {
                "batch_column": "batch_no",
                "batch_value": "B20260327",
            },
            "table_mappings": [{"source_table": "a", "target_table": "b"}],
            "table_primary_keys": [
                {
                    "source_table": "a",
                    "target_table": "b",
                    "primary_keys": ["id"],
                    "target_primary_keys": ["id2"],
                }
            ],
        },
    }

    request = CreateTaskRequest.model_validate(payload)
    assert request.options.incremental_config is not None
    assert request.options.incremental_config.batch_column == "batch_no"
    assert request.options.incremental_config.time_column is None
