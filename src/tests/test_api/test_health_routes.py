async def test_health_reports_healthy_database(client):
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "PostgreSQL" in body["database"]
