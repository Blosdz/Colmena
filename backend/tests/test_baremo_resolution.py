from tests.test_analysis_orchestrator import prepare_orchestrator_fixture


def _create_scoring_configs(client, fixture) -> None:
    form_id = fixture["form"]["id"]
    instrument_id = fixture["instrument"]["id"]
    dimension_id = fixture["dimension"]["id"]
    questions = fixture["questions"]

    config_response = client.post(
        f"/api/v1/forms/{form_id}/scoring/configs",
        json={
            "instrument_id": instrument_id,
            "name": "Puntaje total de compromiso",
            "code": "engagement_total",
            "scoring_level": "instrument",
            "aggregation_method": "mean",
            "missing_policy": "allow_partial",
            "reverse_scoring_enabled": True,
            "interpretation_enabled": True,
            "config_json": {
                "question_ids": [questions["item_01"]["id"], questions["item_02"]["id"], questions["item_03"]["id"]]
            },
            "bands": [
                {"label": "Bajo", "code": "low", "min_value": 0.0, "max_value": 33.32, "interpretation": "Nivel bajo"},
                {"label": "Medio", "code": "medium", "min_value": 33.34, "max_value": 66.65, "interpretation": "Nivel medio"},
                {"label": "Alto", "code": "high", "min_value": 66.67, "max_value": 100.0, "interpretation": "Nivel alto"},
            ],
        },
    )
    assert config_response.status_code == 201

    dimension_config = client.post(
        f"/api/v1/forms/{form_id}/scoring/configs",
        json={
            "dimension_id": dimension_id,
            "name": "Puntaje de dimension",
            "code": "engagement_dimension",
            "scoring_level": "dimension",
            "aggregation_method": "mean",
            "missing_policy": "allow_partial",
            "reverse_scoring_enabled": True,
            "interpretation_enabled": True,
        },
    )
    assert dimension_config.status_code == 201


def test_baremo_resolution_endpoint(client):
    fixture = prepare_orchestrator_fixture(client)
    form_id = fixture["form"]["id"]
    _create_scoring_configs(client, fixture)

    response = client.get(f"/api/v1/forms/{form_id}/scoring/baremos/resolution")
    assert response.status_code == 200
    payload = response.json()
    assert payload["form_id"] == form_id
    assert payload["resolved_variables"] == 2

    by_code = {item["scoring_config_name"]: item for item in payload["items"]}
    with_bands = by_code["Puntaje total de compromiso"]
    assert with_bands["baremo_source"] == "configured_bands"
    assert [level["label"] for level in with_bands["levels"]] == ["Bajo", "Medio", "Alto"]
    assert with_bands["valid_n"] > 0
    assert with_bands["mean_score"] is not None
    assert with_bands["mean_level"] in {"Bajo", "Medio", "Alto"}
    classified = sum(level["n"] for level in with_bands["levels"])
    assert 0 < classified <= with_bands["valid_n"]

    without_bands = by_code["Puntaje de dimension"]
    assert without_bands["baremo_source"] == "equal_range_formula"
    assert len(without_bands["levels"]) == 3
    assert without_bands["levels"][0]["min_value"] == 0
    assert without_bands["levels"][-1]["max_value"] == 100


def test_baremo_apa_table_and_full_scan_blocks(client):
    fixture = prepare_orchestrator_fixture(client)
    form_id = fixture["form"]["id"]
    _create_scoring_configs(client, fixture)

    table_response = client.post(
        f"/api/v1/forms/{form_id}/apa-tables/generate",
        json={"table_type": "baremo_variables", "source_type": "live", "form_id": form_id},
    )
    assert table_response.status_code == 200
    table = table_response.json()
    assert table["table_type"] == "baremo_variables"
    assert [column["label"] for column in table["columns"]] == ["Variable", "Nivel", "Rango", "n", "%", "Interpretacion"]
    assert len(table["rows"]) == 6
    assert table["ready_for_word"] is True
    assert table["html"]
    assert table["markdown"]

    scan_response = client.post(
        f"/api/v1/forms/{form_id}/analysis/full-scan",
        json={"alpha": 0.05, "decimals": 3, "include_discarded": False, "score_aggregation": "mean", "store_result": True},
    )
    assert scan_response.status_code == 200
    scan = scan_response.json()
    baremo_blocks = [block for block in scan["apa_table_blocks"] if block["table_type"] == "baremo_variables"]
    assert len(baremo_blocks) == 1
    block = baremo_blocks[0]
    assert block["columns"] == ["Variable", "Nivel", "Rango", "n", "%", "Interpretacion"]
    assert len(block["rows"]) == 6
    assert block["ready_for_apa"] is True
    assert any(
        resolved_block["title"] == "Baremos resueltos por variable"
        for resolved_block in scan["result_blocks"]
        if resolved_block["block_type"] == "scoring"
    )
