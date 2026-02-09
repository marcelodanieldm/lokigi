# Ejemplos y Tutoriales de Integración Lokigi API

## 1. Zapier (Webhooks)

### Paso a paso
1. Ve a [Zapier Webhooks](https://zapier.com/apps/webhook/integrations).
2. Crea un nuevo Zap y elige "Webhooks by Zapier" como trigger.
3. Selecciona "Custom Request".
4. Configura:
   - Method: GET
   - URL: `https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR`
   - Headers:
     - `x-api-key`: `t2-123456`
5. Haz clic en "Test Trigger" para ver la respuesta minificada.
6. Usa los campos `lokigi_score`, `lost_revenue`, `top_3_actions` en los siguientes pasos del Zap.

### Ejemplo de uso en Zapier
- Puedes enviar el resultado a Gmail, Slack, Google Sheets, etc.

---

## 2. Make.com (ex Integromat)

### Paso a paso
1. Ve a [Make.com](https://www.make.com/) y crea un nuevo escenario.
2. Añade un módulo "HTTP > Make a request".
3. Configura:
   - Method: GET
   - URL: `https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR`
   - Headers:
     - `x-api-key`: `t2-123456`
4. Ejecuta el módulo y mapea los campos de la respuesta JSON.
5. Usa los datos en otros módulos (CRM, email, dashboards, etc).

---

## 3. HubSpot (Custom Code Action / Webhook)

### Opción 1: Custom Code Action (Python)
1. En un workflow de HubSpot, añade una acción de "Custom Code".
2. Usa el siguiente código:
```python
import requests
url = "https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR"
headers = {"x-api-key": "t2-123456"}
resp = requests.get(url, headers=headers)
data = resp.json()
output = {
  "lokigi_score": data["lokigi_score"],
  "lost_revenue": data["lost_revenue"],
  "top_3_actions": ", ".join(data["top_3_actions"])
}
```
3. Usa los valores de `output` en el workflow.

### Opción 2: Webhook
1. En HubSpot, crea un workflow y añade una acción de Webhook.
2. Configura:
   - Method: GET
   - URL: `https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR`
   - Headers:
     - `x-api-key`: `t2-123456`
3. Usa los datos recibidos en los siguientes pasos del workflow.

---

## 4. n8n (No-code Automation)

### Paso a paso
1. Añade un nodo "HTTP Request" en tu workflow de n8n.
2. Configura:
   - Method: GET
   - URL: `https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR`
   - Headers:
     - `x-api-key`: `t2-123456`
3. Usa los datos de la respuesta en nodos siguientes (email, CRM, etc).

---

## 5. Pipedream

### Paso a paso
1. Crea un nuevo workflow en [Pipedream](https://pipedream.com/).
2. Añade un paso de código (Node.js):
```js
import axios from "axios";
export default defineComponent({
  async run({ steps, $ }) {
    const resp = await axios.get("https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR", {
      headers: { "x-api-key": "t2-123456" }
    });
    return resp.data;
  }
});
```
3. Usa los datos en pasos siguientes.

---

## 6. Microsoft Power Automate

### Paso a paso
1. Añade un paso "HTTP" en tu flujo.
2. Configura:
   - Method: GET
   - URL: `https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR`
   - Headers:
     - Key: `x-api-key`, Value: `t2-123456`
3. Usa los datos de la respuesta en acciones siguientes (Teams, SharePoint, etc).

---

## 7. Google Apps Script (Google Sheets, Gmail, etc)

### Ejemplo de código
```javascript
function getLokigiAudit() {
  var url = "https://api.lokigi.com/api/v1/audit?business_id=abc123&lang=es&currency=EUR";
  var options = {
    "method": "get",
    "headers": { "x-api-key": "t2-123456" }
  };
  var response = UrlFetchApp.fetch(url, options);
  var data = JSON.parse(response.getContentText());
  Logger.log(data);
  // Puedes escribir los datos en una hoja de cálculo, enviar email, etc.
}
```

---

> Todos los ejemplos pueden adaptarse a cualquier plataforma que soporte HTTP y JSON. Cambia los parámetros según tu caso de uso y consulta la documentación de la plataforma para detalles de autenticación y manejo de datos.
