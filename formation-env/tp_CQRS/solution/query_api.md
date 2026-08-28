# Explication — Query API

La Query API expose uniquement des lectures sur le Read Model MongoDB.

- `GET /orders/<order_id>` retourne une commande ;
- `GET /customers/<customer_id>/orders` retourne les commandes d'un client.

La projection MongoDB retire `_id` du résultat JSON, mais ne supprime évidemment pas ce champ de la base.
