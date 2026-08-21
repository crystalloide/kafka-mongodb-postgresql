db = db.getSiblingDB("training");
print(`Base de données active : ${db.getName()}`);

// On prend une commande confirmée avec au moins 2 lignes (items.1 existe)
const doc = db.orders.findOne({ status: "CONFIRMED", "items.1": { $exists: true } });

print("=== AVANT $unwind : 1 document ===");
printjson(doc);

print(`\n=== APRÈS $unwind : ${doc.items.length} documents attendus ===`);
const result = db.orders.aggregate([
  { $match: { _id: doc._id } },
  { $unwind: "$items" }
]).toArray();

print(`Nombre de documents obtenus : ${result.length}\n`);
result.forEach((d, i) => {
  print(`--- document ${i + 1} ---`);
  printjson(d);
});
