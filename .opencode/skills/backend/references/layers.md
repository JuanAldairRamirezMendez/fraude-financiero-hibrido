# Capas backend

- `api/v1/routes`: validacion, DI y traduccion HTTP.
- `services`: casos de uso y transacciones.
- `domain`: entidades y reglas puras.
- `repositories`: Protocols e implementaciones SQLite/archivo.
- `schemas`: contratos Pydantic de entrada/salida.

Una dependencia debe apuntar hacia dentro; el dominio no conoce infraestructura.
