# Dashboard Integration

## Guardar mensajes en Dashboard

Para guardar mensajes importantes en el Dashboard, usa:

```
/save Este es un mensaje importante #tag
```

O simplemente dime "guarda esto en el dashboard" seguido del mensaje.

---

## API Endpoint

```
POST http://192.168.1.223:5002/api/telegram/save
Content-Type: application/json

{
  "content": "Tu mensaje",
  "tags": "importante, telegram"
}
```

---

## Repositorio

🔗 https://github.com/polidisio/Dashboard
