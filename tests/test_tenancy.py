"""Multi-tenancy: per-user data isolation and auth enforcement on the
tenant-scoped endpoints (watchlist + alerts run through the request session,
so they isolate cleanly in the test DB)."""

PROTECTED = [
    ("get", "/api/watchlist"),
    ("get", "/api/portfolio"),
    ("get", "/api/alerts"),
    ("get", "/api/alerts/events"),
    ("get", "/api/research/history"),
]


class TestAuthRequired:
    def test_protected_endpoints_401_without_token(self, client):
        for method, path in PROTECTED:
            r = getattr(client, method)(path)
            assert r.status_code == 401, f"{path} should require auth, got {r.status_code}"


class TestWatchlistIsolation:
    def test_users_only_see_their_own_watchlist(self, register, client):
        a = register("a@example.com")
        b = register("b@example.com")

        # A tracks TCS
        assert client.post("/api/watchlist", json={"symbol": "TCS"}, headers=a).status_code == 201

        a_list = client.get("/api/watchlist", headers=a).json()
        b_list = client.get("/api/watchlist", headers=b).json()
        assert [i["symbol"] for i in a_list] == ["TCS"]
        assert b_list == []  # B sees nothing of A's

    def test_one_user_cannot_remove_anothers_item(self, register, client):
        a = register("a@example.com")
        b = register("b@example.com")
        client.post("/api/watchlist", json={"symbol": "TCS"}, headers=a)

        # B tries to remove TCS — only affects B's (empty) watchlist
        client.delete("/api/watchlist/TCS", headers=b)
        a_list = client.get("/api/watchlist", headers=a).json()
        assert [i["symbol"] for i in a_list] == ["TCS"]  # A's item survives


class TestAlertIsolation:
    def test_alert_rules_are_per_user(self, register, client):
        a = register("a@example.com")
        b = register("b@example.com")

        r = client.post("/api/alerts",
                        json={"symbol": "TCS", "kind": "price_above", "threshold": 5000},
                        headers=a)
        assert r.status_code == 201, r.text

        assert len(client.get("/api/alerts", headers=a).json()) == 1
        assert client.get("/api/alerts", headers=b).json() == []

    def test_user_cannot_delete_anothers_rule(self, register, client):
        a = register("a@example.com")
        b = register("b@example.com")
        rule = client.post("/api/alerts",
                           json={"symbol": "TCS", "kind": "buy_signal"},
                           headers=a).json()

        client.delete(f"/api/alerts/{rule['id']}", headers=b)  # B can't touch A's rule
        assert len(client.get("/api/alerts", headers=a).json()) == 1
