CQRS
├── Command Side
│   └── PostgreSQL — Write Model
└── Query Side
    └── MongoDB — Read Model


- Kafka = transport des événements
- Outbox = fiabilité entre PostgreSQL et Kafka
- Projector = construction du Read Model
