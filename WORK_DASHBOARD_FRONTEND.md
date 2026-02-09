# 🎨 Work Dashboard - Documentación Frontend

## 📍 Ubicación
**Ruta:** `/dashboard/work`  
**Archivo:** `frontend/src/app/dashboard/work/page.tsx`

---

## 🎯 Descripción General

Dashboard profesional estilo **Linear/Vercel** para que el equipo de trabajo gestione órdenes de servicio pagadas ($99). Interfaz oscura, minimalista y enfocada en productividad.

---

## 🏗️ Arquitectura del Componente

### Layout Principal

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (Sticky)                                             │
│ Work Queue · 5 órdenes activas · 28 tareas pendientes      │
└─────────────────────────────────────────────────────────────┘
┌──────────────────────────┬──────────────────────────────────┐
│                          │                                  │
│  WORK QUEUE TABLE       │   ORDER DETAIL PANEL             │
│  (Left - 50%)           │   (Right - 50% - Fixed)          │
│                          │                                  │
│  ┌──────────────────┐   │   ┌────────────────────────┐     │
│  │ Cliente 1        │   │   │ Business Info          │     │
│  │ ⏰ 2d  ████ 45%  │   │   │ • Google Maps Link     │     │
│  └──────────────────┘   │   │ • Phone                │     │
│                          │   │ • Score (RED)          │     │
│  ┌──────────────────┐   │   └────────────────────────┘     │
│  │ Cliente 2        │   │                                  │
│  │ ⏰ 6h  ████ 80%  │◄──┤   ┌────────────────────────┐     │
│  └──────────────────┘   │   │ Tasks Checklist        │     │
│                          │   │ ☑ Task 1 [SEO] P10     │     │
│  ┌──────────────────┐   │   │ ☐ Task 2 [CONT] P8     │     │
│  │ Cliente 3        │   │   │ ☐ Task 3 [VERIF] P5    │     │
│  │ ⏰ 1h  ████ 12%  │   │   └────────────────────────┘     │
│  └──────────────────┘   │                                  │
│                          │   ┌────────────────────────┐     │
│                          │   │ Internal Notes         │     │
│                          │   │ [textarea]             │     │
│                          │   └────────────────────────┘     │
│                          │                                  │
│                          │   [Finalizar y Enviar] 🟢       │
└──────────────────────────┴──────────────────────────────────┘
```

---

## 🎨 Secciones del Dashboard

### 1. Header Bar (Sticky)
```tsx
<Header>
  - Título: "Work Queue"
  - Subtítulo: "5 órdenes activas · 28 tareas pendientes"
  - Status indicator: 🟢 Sistema activo (pulsante)
</Header>
```

**Diseño:**
- Background: `bg-black/50 backdrop-blur-sm`
- Border: `border-b border-gray-800`
- Sticky: `sticky top-0 z-40`

---

### 2. Work Queue Table (Left Panel)

**Columnas:**

| Cliente/Negocio | Urgencia | Progreso | Acción |
|-----------------|----------|----------|--------|
| 40%            | 20%      | 30%      | 10%    |

**Row Data:**
```tsx
<OrderRow>
  - Client Name (bold white)
  - Business Name (gray 400)
  - Order # + Score badge (red)
  - Urgency badge: <1h 🟢 | 1-24h 🟡 | 24-48h 🟠 | >48h 🔴
  - Progress bar: 0-100% gradient (blue→purple)
  - Arrow button →
</OrderRow>
```

**Estados:**
- Hover: `hover:bg-gray-900/50`
- Selected: `bg-gray-900/80 border-l-2 border-blue-500`
- Empty state: Checkmark icon + "No hay órdenes pendientes 🎉"

---

### 3. Order Detail Panel (Right Panel - Fixed)

**Layout:**
```tsx
<Panel className="fixed right-6 top-[120px] bottom-6">
  <Header>
    - Business Name (xl bold)
    - Client Name (sm gray)
    - Close button (X)
  </Header>
  
  <ScrollableContent>
    <BusinessInfo />
    <TasksChecklist />
    <InternalNotes />
  </ScrollableContent>
  
  <Footer>
    <CompleteButton />
  </Footer>
</Panel>
```

#### 3.1 Business Info Section

**Google Maps Card:**
```tsx
<Card className="bg-blue-500/5 border-blue-500/20">
  <MapPin icon />
  "Ver en Google Maps"
  <ExternalLink icon />
</Card>
```

**Phone Card:**
```tsx
<Card className="bg-gray-800/30 border-gray-700">
  <Phone icon />
  {client_phone}
</Card>
```

**Score Card (RED ALERT):**
```tsx
<Card className="bg-red-500/5 border-red-500/20">
  <AlertCircle icon />
  "Score Inicial de Visibilidad"
  <Score className="text-3xl font-bold text-red-400">
    35/100
  </Score>
  "Objetivo: Llevar a 85+"
</Card>
```

#### 3.2 Tasks Checklist Section

**Progress Bar:**
```tsx
<ProgressSection>
  <Label>Progreso General</Label>
  <Percentage>75%</Percentage>
  <ProgressBar className="h-3 bg-gradient(blue→purple→pink)" />
</ProgressSection>
```

**Task Item:**
```tsx
<TaskCard className={is_completed ? "bg-green-500/5" : "bg-gray-800/30"}>
  <Checkbox onClick={toggleTask}>
    {is_completed ? <CheckCircle2 /> : <Circle />}
  </Checkbox>
  
  <Description className={is_completed && "line-through"}>
    {task.description}
  </Description>
  
  <Badges>
    <CategoryBadge>{SEO|CONTENIDO|VERIFICACION}</CategoryBadge>
    <PriorityBadge>P{1-10}</PriorityBadge>
  </Badges>
</TaskCard>
```

**Category Colors:**
- SEO: `bg-blue-500/10 text-blue-400 border-blue-500/20`
- CONTENIDO: `bg-purple-500/10 text-purple-400 border-purple-500/20`
- VERIFICACION: `bg-green-500/10 text-green-400 border-green-500/20`

**Priority Colors:**
- P9-10: `bg-red-500/10 text-red-400` 🔴
- P7-8: `bg-orange-500/10 text-orange-400` 🟠
- P5-6: `bg-yellow-500/10 text-yellow-400` 🟡
- P1-4: `bg-gray-500/10 text-gray-400` ⚪

#### 3.3 Internal Notes

```tsx
<NotesSection>
  <Label>Notas Internas</Label>
  <Textarea
    value={internalNotes}
    onChange={setInternalNotes}
    placeholder="Escribe notas sobre el progreso..."
    className="h-32 bg-gray-800/50 border-gray-700"
  />
</NotesSection>
```

#### 3.4 Complete Button

**Estado Habilitado (100% completado):**
```tsx
<Button className="bg-gradient-to-r from-green-600 to-emerald-600">
  <Send icon />
  Finalizar y Enviar Reporte de Éxito
</Button>
```

**Estado Deshabilitado (<100%):**
```tsx
<Button className="bg-gray-800 opacity-50 cursor-not-allowed">
  Finalizar y Enviar Reporte de Éxito
</Button>
<Helper>
  Completa todas las tareas ({pending} pendientes)
</Helper>
```

---

## 🎨 Color Palette

```css
/* Background */
--bg-primary: #0A0A0A;
--bg-secondary: #111111;
--bg-tertiary: #000000;

/* Borders */
--border-primary: #1F1F1F (gray-800);
--border-secondary: #2A2A2A (gray-700);

/* Text */
--text-primary: #FFFFFF;
--text-secondary: #9CA3AF (gray-400);
--text-tertiary: #6B7280 (gray-500);

/* Status Colors */
--red: #EF4444 / 10% (bg) / 20% (border);
--orange: #F59E0B / 10% / 20%;
--yellow: #FBBF24 / 10% / 20%;
--green: #10B981 / 10% / 20%;
--blue: #3B82F6 / 10% / 20%;
--purple: #8B5CF6 / 10% / 20%;
```

---

## 🔌 API Integration

### 1. Fetch Orders (On Mount)
```typescript
GET /api/dashboard/orders
→ Filter by status === 'completed' (órdenes pagadas)
```

### 2. Fetch Tasks (On Order Select)
```typescript
GET /api/dashboard/orders/{order_id}/tasks
→ Returns: { tasks[], completion_percentage, pending_tasks }
```

### 3. Toggle Task (On Checkbox Click)
```typescript
PATCH /api/dashboard/tasks/{task_id}
Body: {
  is_completed: true/false,
  notes: "Completado desde dashboard"
}
→ Refresh tasks after success
```

### 4. Complete Order (On Button Click)
```typescript
POST /api/dashboard/orders/{order_id}/complete
Body: {
  notes: internalNotes
}
→ Success: Alert + Refresh orders + Close panel
```

---

## ⚡ Features & Interactions

### Responsiveness
- **Desktop (1800px+):** Split view 50/50
- **Tablet/Mobile:** Stack vertically (TODO)

### Animations
- Smooth transitions: `transition-all duration-300`
- Progress bars: `duration-500`
- Pulse effect: Status indicator (green dot)
- Hover effects: `hover:bg-gray-900/50`

### Loading States
```tsx
<Loader2 className="w-8 h-8 animate-spin" />
```

### Empty States
```tsx
<EmptyState>
  <CheckCircle2 className="w-12 h-12 text-gray-600" />
  "No hay órdenes pendientes"
  "Todas las tareas están completadas 🎉"
</EmptyState>
```

---

## 🚀 Key UX Decisions

1. **Fixed Right Panel:** El panel de detalle es fixed para que siempre esté visible mientras scrolleas la lista de órdenes.

2. **Urgency Colors:** Sistema de 4 niveles de urgencia basado en tiempo transcurrido:
   - 🟢 <24h: Fresh, no rush
   - 🟡 24-48h: Medium priority
   - 🟠 48-72h: High priority
   - 🔴 >72h: URGENT - cliente esperando mucho

3. **Score in Red:** El score inicial siempre se muestra en rojo para crear sensación de urgencia y mostrar el problema que debe resolverse.

4. **Progress Gradient:** El gradiente azul→morado→rosa es visualmente atractivo y transmite progreso positivo.

5. **Checkbox Instant Feedback:** Al hacer click en una tarea, se actualiza inmediatamente (optimistic update) mientras se sincroniza con el backend.

6. **Complete Button Disabled:** Solo se puede finalizar cuando el 100% está hecho. Esto asegura calidad y no deja tareas incompletas.

---

## 📱 Mobile Considerations (TODO)

Para versión mobile, cambiar layout:

```tsx
// Desktop
<div className="flex gap-6">
  <WorkQueue className="w-1/2" />
  <DetailPanel className="w-1/2 fixed" />
</div>

// Mobile
<div className="flex flex-col">
  {!selectedOrder && <WorkQueue className="w-full" />}
  {selectedOrder && <DetailPanel className="w-full" />}
</div>
```

---

## 🎯 Testing Checklist

- [ ] Cargar órdenes pagadas
- [ ] Seleccionar orden → ver detalle
- [ ] Toggle tarea → actualiza progreso
- [ ] Completar todas las tareas → botón se habilita
- [ ] Click "Finalizar" → envía orden y cierra panel
- [ ] Urgency badges cambian según tiempo
- [ ] Progress bar se actualiza en tiempo real
- [ ] Notas internas se guardan correctamente
- [ ] Link a Google Maps funciona
- [ ] Empty state cuando no hay órdenes

---

## 🔥 Pro Tips

1. **Keep it Simple:** No agregar más features. La interfaz debe ser ultra-productiva y sin distracciones.

2. **Performance:** Usar React.memo() si la lista de órdenes crece mucho (>50).

3. **Real-time Updates:** Considerar WebSocket para actualizar tareas en tiempo real si múltiples trabajadores están en el mismo proyecto.

4. **Keyboard Shortcuts:** Agregar atajos de teclado:
   - `Esc`: Cerrar panel
   - `Ctrl + Enter`: Completar orden
   - `Space`: Toggle tarea seleccionada

5. **Sound Effects:** Agregar sonido sutil cuando se completa una tarea o una orden (opcional, puede ser molesto).

---

## 🎨 Inspiración de Diseño

Este dashboard está inspirado en:
- **Linear:** Clean, dark, productive
- **Vercel Dashboard:** Minimalist, elegant
- **GitHub Projects:** Card-based, status-driven
- **Notion:** Simple checkboxes, good hierarchy

**Filosofía:** *"Menos es más. Muestra solo lo esencial."*

---

## 📝 Notas de Implementación

### Decisiones técnicas:

1. **Todo en un solo archivo:** Mantener todo en `page.tsx` por simplicidad. Si crece, separar en componentes.

2. **No usar Context API:** Por ahora, state local es suficiente. Si múltiples rutas necesitan el selectedOrder, considerar Context.

3. **Fetch on demand:** Solo carga tasks cuando seleccionas una orden. Ahorra bandwidth.

4. **Optimistic updates:** Cuando toggleas una tarea, actualiza el UI inmediatamente sin esperar el backend response.

5. **Fixed positioning:** El panel derecho usa `fixed` en lugar de `sticky` para mejor control del scroll independiente.

---

## 🚀 Next Steps

1. Agregar filtros en Work Queue:
   - Por urgencia (🔴🟠🟡🟢)
   - Por progreso (0-25%, 25-50%, 50-75%, 75-100%)
   - Por cliente (search)

2. Agregar search bar para buscar órdenes por nombre de cliente o negocio.

3. Agregar sort options:
   - Por urgencia (más urgentes primero)
   - Por progreso (menos avanzados primero)
   - Por fecha de pago

4. Agregar bulk actions:
   - Seleccionar múltiples órdenes
   - Asignar a trabajador específico
   - Agregar notas a múltiples órdenes

5. Agregar notificaciones push cuando hay nueva orden pagada.

---

**Última actualización:** 2024-12-19  
**Autor:** Lokigi Team  
**Status:** ✅ Completado y listo para usar
