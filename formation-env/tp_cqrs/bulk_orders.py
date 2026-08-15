for i in $(seq 1 20); do
  curl -X POST http://localhost:5000/orders \
    -H "Content-Type: application/json" \
    -d '{"customer_id": "CUST-'"$i"'", "items": [
           {"product_id": "P-001", "quantity": 1, "unit_price": 79.9}
        ]}'
done