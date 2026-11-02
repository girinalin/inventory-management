from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Literal, Optional
from pydantic import BaseModel
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders, restocking_orders
import itertools
from datetime import datetime

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

# Lead time in days per inventory category (for restocking feature)
# Categories enumerated from server/data/inventory.json
CATEGORY_LEAD_TIMES = {
    'Actuators': 12,
    'Circuit Boards': 14,
    'Controllers': 11,
    'Power Supplies': 9,
    'Sensors': 10,
}
DEFAULT_LEAD_TIME_DAYS = 10

def get_lead_time(category: str) -> int:
    return CATEGORY_LEAD_TIMES.get(category, DEFAULT_LEAD_TIME_DAYS)

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False
    # The Dashboard keys its Create PO / View PO button off this id
    purchase_order_id: Optional[str] = None

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

# camelCase field names (dueDate) match the client's task objects, not snake_case
class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: Literal["low", "medium", "high"] = "medium"
    dueDate: str

class RestockingRecommendation(BaseModel):
    sku: str
    name: str
    category: str
    current_demand: int
    forecasted_demand: int
    demand_gap: int
    unit_cost: float
    suggested_quantity: int
    line_total: float
    lead_time_days: int

class RestockingRecommendationsResponse(BaseModel):
    budget: float
    items: List[RestockingRecommendation]
    total_cost: float
    remaining_budget: float

class RestockingOrderLineItem(BaseModel):
    sku: str
    name: str
    quantity: int
    unit_cost: float
    category: str
    lead_time_days: int

class CreateRestockingOrderRequest(BaseModel):
    items: List[RestockingOrderLineItem]
    budget: float

class RestockingOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockingOrderLineItem]
    total_cost: float
    budget: float
    status: str
    lead_time_days: int
    created_date: str

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        po = next((po for po in purchase_orders if po["backlog_item_id"] == item["id"]), None)
        item_dict["has_purchase_order"] = po is not None
        item_dict["purchase_order_id"] = po["id"] if po else None
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

# Restocking feature endpoints
_restocking_order_seq = itertools.count(1)

@app.get("/api/restocking/recommendations", response_model=RestockingRecommendationsResponse)
def get_restocking_recommendations(budget: float = 25000):
    """Get restocking recommendations based on budget and demand forecast.
    Recommends increasing-trend items by demand gap, constrained to budget."""
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative")

    # Build sku -> inventory record lookup for unit costs and categories
    inventory_by_sku = {item["sku"]: item for item in inventory_items}

    # Candidates: increasing-trend forecasts with positive demand gap
    candidates = []
    for f in demand_forecasts:
        if f.get("trend") != "increasing":
            continue
        gap = f["forecasted_demand"] - f["current_demand"]
        if gap <= 0:
            continue
        inv = inventory_by_sku.get(f["item_sku"])
        if not inv:
            continue
        candidates.append({
            "sku": f["item_sku"],
            "name": f["item_name"],
            "category": inv["category"],
            "current_demand": f["current_demand"],
            "forecasted_demand": f["forecasted_demand"],
            "demand_gap": gap,
            "unit_cost": inv["unit_cost"],
            "suggested_quantity": gap,  # restock quantity = full demand gap
        })

    # Sort descending by demand gap
    candidates.sort(key=lambda c: c["demand_gap"], reverse=True)

    # Greedily add items while within budget (skip, don't stop, on over-budget items)
    selected = []
    running_total = 0.0
    for c in candidates:
        line_total = round(c["suggested_quantity"] * c["unit_cost"], 2)
        if running_total + line_total > budget:
            continue  # Skip this item, but keep checking smaller/cheaper ones
        running_total += line_total
        selected.append(RestockingRecommendation(
            sku=c["sku"], name=c["name"], category=c["category"],
            current_demand=c["current_demand"], forecasted_demand=c["forecasted_demand"],
            demand_gap=c["demand_gap"], unit_cost=c["unit_cost"],
            suggested_quantity=c["suggested_quantity"], line_total=line_total,
            lead_time_days=get_lead_time(c["category"]),
        ))

    return RestockingRecommendationsResponse(
        budget=budget, items=selected,
        total_cost=round(running_total, 2),
        remaining_budget=round(budget - running_total, 2),
    )

@app.post("/api/restocking/orders", response_model=RestockingOrder, status_code=201)
def create_restocking_order(payload: CreateRestockingOrderRequest):
    """Submit a restocking order with selected items and budget.
    Returns the created order with lead time (max across line items)."""
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    total_cost = round(sum(i.quantity * i.unit_cost for i in payload.items), 2)
    if total_cost > payload.budget:
        raise HTTPException(status_code=400, detail="Order total exceeds budget")

    # Lead time is the maximum across all line items
    max_lead_time = max(i.lead_time_days for i in payload.items)
    seq = next(_restocking_order_seq)

    order = {
        "id": f"RSO-{seq:04d}",
        "order_number": f"RESTOCK-{seq:04d}",
        "items": [i.dict() for i in payload.items],
        "total_cost": total_cost,
        "budget": payload.budget,
        "status": "Submitted",
        "lead_time_days": max_lead_time,
        "created_date": datetime.utcnow().strftime("%Y-%m-%d"),
    }
    restocking_orders.append(order)
    return order

@app.get("/api/restocking/orders", response_model=List[RestockingOrder])
def get_restocking_orders():
    """Get all submitted restocking orders"""
    return restocking_orders

# Tasks feature endpoints
# Tasks live only in memory and start empty; the client merges them with its
# local mock tasks, so IDs are prefixed to avoid colliding with those mocks.
_task_seq = itertools.count(1)
tasks: List[dict] = []

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get all API-managed tasks"""
    return tasks

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(payload: CreateTaskRequest):
    """Create a task. New tasks start as pending and go to the front of the list."""
    task = {
        "id": f"api-task-{next(_task_seq)}",
        "title": payload.title,
        "priority": payload.priority,
        "dueDate": payload.dueDate,
        "status": "pending",
    }
    tasks.insert(0, task)
    return task

# PATCH takes no body: the only update the client makes is flipping status.
@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    index = next((i for i, t in enumerate(tasks) if t["id"] == task_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks.pop(index)
    return {"success": True}

# Purchase order endpoints
_purchase_order_seq = itertools.count(1)

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(payload: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item.
    Only one PO per backlog item: the Dashboard's 'Create PO' button is
    replaced by 'View PO' once a PO exists, so a second create is a conflict."""
    if not any(item["id"] == payload.backlog_item_id for item in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {payload.backlog_item_id} not found")
    if payload.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
    if payload.unit_cost < 0:
        raise HTTPException(status_code=400, detail="Unit cost cannot be negative")
    if any(po["backlog_item_id"] == payload.backlog_item_id for po in purchase_orders):
        raise HTTPException(status_code=409, detail="A purchase order already exists for this backlog item")

    po = {
        "id": f"PO-{next(_purchase_order_seq):04d}",
        "backlog_item_id": payload.backlog_item_id,
        "supplier_name": payload.supplier_name,
        "quantity": payload.quantity,
        "unit_cost": payload.unit_cost,
        "expected_delivery_date": payload.expected_delivery_date,
        "status": "Submitted",
        "created_date": datetime.utcnow().strftime("%Y-%m-%d"),
        "notes": payload.notes,
    }
    purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order for a backlog item"""
    po = next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)
    if po is None:
        raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")
    return po

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
