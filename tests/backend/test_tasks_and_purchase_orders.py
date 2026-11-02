"""
Tests for tasks and purchase-order API endpoints.

Both features keep state in module-level lists in server/main.py, so the
autouse fixture snapshots and restores that state around every test to keep
tests independent of each other and of run order.
"""
import pytest

import main


@pytest.fixture(autouse=True)
def restore_mutable_state():
    """Restore in-memory task and purchase-order state after each test."""
    saved_tasks = list(main.tasks)
    saved_pos = list(main.purchase_orders)
    yield
    main.tasks[:] = saved_tasks
    main.purchase_orders[:] = saved_pos


def _backlog_item_without_po():
    """Pick a backlog item that has no purchase order yet."""
    po_ids = {po["backlog_item_id"] for po in main.purchase_orders}
    for item in main.backlog_items:
        if item["id"] not in po_ids:
            return item["id"]
    pytest.skip("All backlog items already have purchase orders")


def _po_payload(backlog_item_id, **overrides):
    payload = {
        "backlog_item_id": backlog_item_id,
        "supplier_name": "Acme Components",
        "quantity": 100,
        "unit_cost": 12.5,
        "expected_delivery_date": "2026-12-10",
        "notes": None,
    }
    payload.update(overrides)
    return payload


class TestTasksEndpoints:
    """Test suite for the /api/tasks endpoints."""

    def test_get_tasks_returns_list(self, client):
        """Test getting tasks returns a list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_task_returns_pending_task(self, client):
        """Test creating a task returns 201 with the expected structure."""
        response = client.post(
            "/api/tasks",
            json={"title": "Recount bin A-12", "priority": "high", "dueDate": "2026-12-01"},
        )
        assert response.status_code == 201

        task = response.json()
        assert task["title"] == "Recount bin A-12"
        assert task["priority"] == "high"
        assert task["dueDate"] == "2026-12-01"
        assert task["status"] == "pending"
        assert task["id"].startswith("api-task-")

    def test_create_task_defaults_priority_to_medium(self, client):
        """Test priority defaults to medium when omitted."""
        response = client.post(
            "/api/tasks", json={"title": "Call supplier", "dueDate": "2026-12-01"}
        )
        assert response.status_code == 201
        assert response.json()["priority"] == "medium"

    def test_create_task_rejects_unknown_priority(self, client):
        """Test priority outside low/medium/high is rejected."""
        response = client.post(
            "/api/tasks",
            json={"title": "x", "priority": "urgent", "dueDate": "2026-12-01"},
        )
        assert response.status_code == 422

    def test_new_task_appears_first_in_list(self, client):
        """Test newly created tasks go to the front of the list."""
        client.post("/api/tasks", json={"title": "First", "dueDate": "2026-12-01"})
        second = client.post(
            "/api/tasks", json={"title": "Second", "dueDate": "2026-12-02"}
        ).json()

        tasks = client.get("/api/tasks").json()
        assert tasks[0]["id"] == second["id"]

    def test_toggle_task_flips_status(self, client):
        """Test PATCH toggles a task between pending and completed."""
        task = client.post(
            "/api/tasks", json={"title": "Toggle me", "dueDate": "2026-12-01"}
        ).json()

        first = client.patch(f"/api/tasks/{task['id']}")
        assert first.status_code == 200
        assert first.json()["status"] == "completed"

        second = client.patch(f"/api/tasks/{task['id']}")
        assert second.json()["status"] == "pending"

    def test_toggle_nonexistent_task(self, client):
        """Test toggling a task that doesn't exist returns 404."""
        response = client.patch("/api/tasks/api-task-does-not-exist")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_task_removes_it(self, client):
        """Test deleting a task removes it from the list."""
        task = client.post(
            "/api/tasks", json={"title": "Delete me", "dueDate": "2026-12-01"}
        ).json()

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 200

        ids = [t["id"] for t in client.get("/api/tasks").json()]
        assert task["id"] not in ids

    def test_delete_nonexistent_task(self, client):
        """Test deleting a task that doesn't exist returns 404."""
        response = client.delete("/api/tasks/api-task-does-not-exist")
        assert response.status_code == 404


class TestPurchaseOrderEndpoints:
    """Test suite for the /api/purchase-orders endpoints."""

    def test_create_purchase_order(self, client):
        """Test creating a PO for a backlog item returns 201 with the PO."""
        backlog_id = _backlog_item_without_po()
        response = client.post("/api/purchase-orders", json=_po_payload(backlog_id))
        assert response.status_code == 201

        po = response.json()
        assert po["id"].startswith("PO-")
        assert po["backlog_item_id"] == backlog_id
        assert po["quantity"] == 100
        assert po["status"] == "Submitted"

    def test_create_purchase_order_unknown_backlog_item(self, client):
        """Test creating a PO for a missing backlog item returns 404."""
        response = client.post(
            "/api/purchase-orders",
            json=_po_payload("backlog-does-not-exist"),
        )
        assert response.status_code == 404

    def test_create_purchase_order_rejects_zero_quantity(self, client):
        """Test a zero quantity is rejected with 400."""
        backlog_id = _backlog_item_without_po()
        response = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_id, quantity=0)
        )
        assert response.status_code == 400

    def test_create_purchase_order_rejects_negative_unit_cost(self, client):
        """Test a negative unit cost is rejected with 400."""
        backlog_id = _backlog_item_without_po()
        response = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_id, unit_cost=-1)
        )
        assert response.status_code == 400

    def test_second_purchase_order_for_same_item_conflicts(self, client):
        """Test only one PO per backlog item: a second create returns 409."""
        backlog_id = _backlog_item_without_po()
        first = client.post("/api/purchase-orders", json=_po_payload(backlog_id))
        assert first.status_code == 201

        second = client.post("/api/purchase-orders", json=_po_payload(backlog_id))
        assert second.status_code == 409

    def test_get_purchase_order_by_backlog_item(self, client):
        """Test fetching the PO for a backlog item returns the created PO."""
        backlog_id = _backlog_item_without_po()
        created = client.post(
            "/api/purchase-orders", json=_po_payload(backlog_id)
        ).json()

        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 200
        assert response.json()["id"] == created["id"]

    def test_get_purchase_order_missing_returns_404(self, client):
        """Test fetching a PO for a backlog item without one returns 404."""
        backlog_id = _backlog_item_without_po()
        response = client.get(f"/api/purchase-orders/{backlog_id}")
        assert response.status_code == 404

    def test_backlog_reflects_created_purchase_order(self, client):
        """Test /api/backlog flags an item once it has a PO."""
        backlog_id = _backlog_item_without_po()
        client.post("/api/purchase-orders", json=_po_payload(backlog_id))

        items = client.get("/api/backlog").json()
        flagged = next(item for item in items if item["id"] == backlog_id)
        assert flagged["has_purchase_order"] is True
        # The Dashboard needs the id itself to switch to "View PO" after a reload
        assert flagged["purchase_order_id"] == created_id(client, backlog_id)


def created_id(client, backlog_id):
    return client.get(f"/api/purchase-orders/{backlog_id}").json()["id"]
