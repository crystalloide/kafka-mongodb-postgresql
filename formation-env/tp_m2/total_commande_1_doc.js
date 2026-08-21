db = db.getSiblingDB("training");

const doc = db.orders.findOne({ status: "CONFIRMED", "items.1": { $exists: true } });

print("=== Total de la commande via $sum + $map (sans $unwind) ===");
const result = db.orders.aggregate([
  { $match: { _id: doc._id } },
  {
    $project: {
      _id: 1,
      items: 1,
      order_total: {
        $sum: {
          $map: {
            input: "$items",
            as: "it",
            in: { $multiply: ["$$it.unit_price", "$$it.quantity"] }
          }
        }
      }
    }
  }
]).toArray();

printjson(result[0]);
